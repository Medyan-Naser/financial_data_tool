"""
PARSING PIPELINE ORCHESTRATOR

Implements the full workflow:
1. Extract table → 2. Regex Candidates → 3. Numerical Cross-Check (10% margin) 
→ 4. Summation Verification → 5. LLM Agent Tie-breaking → 6. Final Consolidated Output

This module ties together:
- HybridMatcher (regex + CamelCase candidates)
- TemporalValidator (10% cross-year rule)
- SummationChecker (sum-check utility)
- AgentOrchestrator (LLM tie-breaking)

Usage:
    from pipeline import ParsingPipeline
    pipeline = ParsingPipeline(
        statement_map=IncomeStatementMap(),
        og_df=original_dataframe,
        rows_text=rows_text_dict,
        rows_that_are_sum=sum_rows,
        cal_facts=xml_equations,
        historical_statements=historical_data,
    )
    mapped_df = pipeline.run()
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field

from hybrid_matcher import HybridMatcher, MatchCandidate, decompose_gaap_tag
from temporal_validator import TemporalValidator
from summation_checker import SummationChecker
from agents import AgentOrchestrator, check_ollama_available
from statement_maps import MapFact

logger = logging.getLogger(__name__)


# ─── Configuration ─────────────────────────────────────────────────────────────

@dataclass
class PipelineConfig:
    """Configuration for the parsing pipeline."""
    # Temporal validation
    temporal_tolerance: float = 0.10      # 10% margin for cross-year matching
    temporal_enabled: bool = True
    
    # Summation checking
    summation_tolerance: float = 0.02     # 2% for sum verification
    summation_enabled: bool = True
    
    # LLM agents
    llm_enabled: bool = True
    llm_model: str = "llama3.2"
    llm_fallback_model: str = "mistral"
    llm_analysis_model: str = "llama3.2" # "deepseek-r1" # takes too long
    llm_base_url: str = "http://localhost:11434"
    
    # Thresholds for invoking LLM (LOWERED to use agents more dynamically)
    llm_ambiguity_threshold: float = 15.0  # Invoke LLM if top 2 candidates within this score gap
    llm_low_confidence_threshold: float = 40.0  # Invoke LLM if best score below this
    
    # Discovery (find missing items via LLM)
    discovery_enabled: bool = True
    
    # Expected key facts per statement type
    expected_facts: Dict[str, List[str]] = field(default_factory=lambda: {
        'income_statement': [
            'Total revenue', 'COGS', 'Gross profit', 'Operating income',
            'Net income', 'Income Tax Expense',
        ],
        'balance_sheet': [
            'Total Assets', 'Total Liabilities', 'Stockholders Equity',
            'Current Assets', 'Current Liabilities',
        ],
        'cash_flow_statement': [
            'Net cash from operating activities',
            'Net cash from investing activities',
            'Net cash from financing activities',
        ],
    })


# ─── Pipeline Results ──────────────────────────────────────────────────────────

@dataclass
class MappingResult:
    """Result for a single row mapping."""
    row_idx: str
    fact_name: str
    pattern_type: str
    total_score: float
    regex_score: float
    temporal_score: float
    summation_score: float
    llm_score: float
    confidence: float
    used_llm: bool
    is_total_row: bool


@dataclass
class PipelineResult:
    """Full result of the parsing pipeline."""
    mapped_df: pd.DataFrame
    mappings: List[MappingResult]
    unmapped_rows: List[str]
    discovered_mappings: List[Dict]
    statistics: Dict
    

# ─── Main Pipeline ─────────────────────────────────────────────────────────────

class ParsingPipeline:
    """
    Orchestrates the full financial statement parsing pipeline.
    
    Workflow:
    1. HybridMatcher generates candidates for every row
    2. TemporalValidator scores candidates using cross-year data
    3. SummationChecker scores candidates using summation logic
    4. For ambiguous matches, LLM agents break the tie
    5. Discovery agent finds missing expected items
    6. Final mapped DataFrame is produced
    """

    def __init__(self, statement_map, og_df: pd.DataFrame,
                 rows_text: Dict[str, str],
                 rows_that_are_sum: List[str],
                 cal_facts: Optional[Dict] = None,
                 historical_statements: Optional[Dict[str, pd.DataFrame]] = None,
                 statement_type: str = 'income_statement',
                 config: Optional[PipelineConfig] = None):
        """
        Args:
            statement_map: IncomeStatementMap, BalanceSheetMap, or CashFlowMap
            og_df: Original DataFrame from the filing
            rows_text: Dict mapping row index -> human-readable label
            rows_that_are_sum: List of row indices marked as sum rows
            cal_facts: Calculation relationships from _cal.xml
            historical_statements: Dict of {year: mapped_df} for cross-year validation
            statement_type: Type of statement being parsed
            config: Pipeline configuration
        """
        self.statement_map = statement_map
        self.og_df = og_df
        self.rows_text = rows_text
        self.rows_that_are_sum = rows_that_are_sum
        self.cal_facts = cal_facts or {}
        self.historical_statements = historical_statements or {}
        self.statement_type = statement_type
        self.config = config or PipelineConfig()
        
        # Initialize components
        self.matcher = HybridMatcher(statement_map)
        self.temporal_validator = TemporalValidator(
            historical_statements,
            tolerance=self.config.temporal_tolerance,
        ) if self.config.temporal_enabled else None
        self.summation_checker = SummationChecker(
            og_df, rows_that_are_sum, cal_facts,
            tolerance=self.config.summation_tolerance,
        ) if self.config.summation_enabled else None
        
        # LLM agents (lazy init - only if needed)
        self._agent_orchestrator = None
        self._ollama_checked = False
        self._ollama_available = False

    def _get_agent(self) -> Optional[AgentOrchestrator]:
        """Lazy-initialize the LLM agent orchestrator."""
        if not self.config.llm_enabled:
            return None
        if self._agent_orchestrator is not None:
            return self._agent_orchestrator
        if not self._ollama_checked:
            self._ollama_checked = True
            self._ollama_available = check_ollama_available(self.config.llm_base_url)
            if not self._ollama_available:
                logger.warning("Ollama not available - LLM agents disabled for this run")
        if not self._ollama_available:
            return None
        self._agent_orchestrator = AgentOrchestrator(
            model_name=self.config.llm_model,
            fallback_model=self.config.llm_fallback_model,
            analysis_model=self.config.llm_analysis_model,
            base_url=self.config.llm_base_url,
        )
        return self._agent_orchestrator

    def run(self) -> PipelineResult:
        """
        Execute the full parsing pipeline.
        
        Returns:
            PipelineResult with mapped DataFrame and metadata
        """
        logger.info(f"[Pipeline] Starting {self.statement_type} ({len(self.og_df)} rows, {len(self.historical_statements)} historical filings)")

        # ── Step 1: Create empty mapped DataFrame ──────────────────────────
        mapped_df = self._create_mapped_df()

        # ── Step 2: Generate regex candidates for every row ────────────────
        logger.info("[Pipeline] Step 2: Generating regex candidates...")
        candidates_by_row = self.matcher.find_all_row_candidates(
            self.og_df, self.rows_text
        )
        
        # Attach row_data to each candidate's context
        for row_idx, candidates in candidates_by_row.items():
            row_data = self.og_df.loc[row_idx]
            for c in candidates:
                c.context['row_data'] = row_data
                c.context['human_label'] = self.rows_text.get(row_idx, '')

        # ── Step 3: Temporal validation ────────────────────────────────────
        if self.temporal_validator and self.historical_statements:
            logger.info("[Pipeline] Step 3: Temporal cross-year validation (%d historical filings)", len(self.historical_statements))
            self.temporal_validator.validate_all_candidates(candidates_by_row)
        else:
            logger.info("[Pipeline] Step 3: Temporal validation skipped (no historical data)")

        # ── Step 4: Summation checking ─────────────────────────────────────
        if self.summation_checker:
            logger.info("[Pipeline] Step 4: Summation verification (%d sum-marked rows)", len(self.rows_that_are_sum))
            self.summation_checker.score_all_candidates(candidates_by_row)
        else:
            logger.info("[Pipeline] Step 4: Summation checking skipped")

        # ── Step 5: Select best candidates & LLM tie-breaking ──────────────
        logger.info("[Pipeline] Step 5: Selecting best matches...")
        mappings = self._select_best_mappings(candidates_by_row, mapped_df)

        # ── Step 6: Discovery of missing items ─────────────────────────────
        discovered = []
        mapped_fact_names = {m.fact_name for m in mappings}
        mapped_row_idxs = {m.row_idx for m in mappings}
        expected = self.config.expected_facts.get(self.statement_type, [])
        missing_facts = [f for f in expected if f not in mapped_fact_names]

        if missing_facts and self.config.discovery_enabled:
            logger.info("[Pipeline] Step 6: LLM Discovery for missing items: %s", missing_facts)
            agent = self._get_agent()
            if agent:
                discoveries = agent.discover_missing_items(
                    self.og_df, self.rows_text,
                    mapped_row_idxs, missing_facts, self.statement_type
                )
                for disc in discoveries:
                    if (disc.suggested_fact and disc.confidence >= 0.6 and
                        disc.suggested_fact in mapped_df.index and
                        disc.row_idx in self.og_df.index):
                        # Apply the discovery
                        mapped_df.loc[disc.suggested_fact] = self.og_df.loc[disc.row_idx]
                        discovered.append({
                            'row_idx': disc.row_idx,
                            'fact': disc.suggested_fact,
                            'confidence': disc.confidence,
                            'reasoning': disc.reasoning,
                        })
                        logger.info(
                            f"  Discovered: '{disc.row_idx}' -> '{disc.suggested_fact}' "
                            f"(conf={disc.confidence:.2f})"
                        )
        else:
            logger.info("[Pipeline] Step 6: Discovery skipped (no missing items or disabled)")

        # ── Compute statistics ─────────────────────────────────────────────
        total_rows = len(self.og_df)
        mapped_rows = len(mappings) + len(discovered)
        non_zero_facts = len(mapped_df.index[(mapped_df != 0).any(axis=1)])
        
        stats = {
            'total_rows': total_rows,
            'mapped_rows': mapped_rows,
            'unmapped_rows': total_rows - mapped_rows,
            'match_percentage': (mapped_rows / total_rows * 100) if total_rows > 0 else 0,
            'non_zero_facts': non_zero_facts,
            'llm_invocations': sum(1 for m in mappings if m.used_llm),
            'discovered_items': len(discovered),
            'missing_expected': [f for f in missing_facts if f not in {d['fact'] for d in discovered}],
        }
        
        unmapped = [idx for idx in self.og_df.index if idx not in mapped_row_idxs]
        
        # ── Detailed logging of results ───────────────────────────
        logger.info(f"[Pipeline] === {self.statement_type} Results ===")
        logger.info(f"[Pipeline] Matched {mapped_rows}/{total_rows} rows ({stats['match_percentage']:.1f}%)")
        
        # Log key mappings
        for m in sorted(mappings, key=lambda x: x.total_score, reverse=True):
            dim_flag = ' [DIM]' if m.row_idx != m.row_idx.split('::')[-1].lstrip('D1:').lstrip('D2:') else ''
            llm_flag = ' [LLM]' if m.used_llm else ''
            logger.info(
                f"[Pipeline]   {m.fact_name:40s} <- {m.row_idx:50s} "
                f"(score={m.total_score:6.1f}, {m.pattern_type}){dim_flag}{llm_flag}"
            )
        
        if stats['llm_invocations'] > 0:
            logger.info(f"[Pipeline] LLM agent invocations: {stats['llm_invocations']}")
        if discovered:
            logger.info(f"[Pipeline] LLM discovered {len(discovered)} missing items:")
            for d in discovered:
                logger.info(f"[Pipeline]   {d['fact']:40s} <- {d['row_idx']} (conf={d['confidence']:.2f})")
        if stats['missing_expected']:
            logger.warning(f"[Pipeline] Still missing expected items: {stats['missing_expected']}")
        if unmapped:
            logger.debug(f"[Pipeline] {len(unmapped)} unmatched rows (use DEBUG to see details)")
            for u in unmapped[:10]:
                logger.debug(f"[Pipeline]   unmatched: {u}  ({self.rows_text.get(u, '')})")
            if len(unmapped) > 10:
                logger.debug(f"[Pipeline]   ... and {len(unmapped) - 10} more")

        return PipelineResult(
            mapped_df=mapped_df,
            mappings=mappings,
            unmapped_rows=unmapped,
            discovered_mappings=discovered,
            statistics=stats,
        )

    def _create_mapped_df(self) -> pd.DataFrame:
        """Create a zeroed DataFrame from the statement map."""
        map_facts = vars(self.statement_map)
        row_labels = [
            mf.fact for mf in map_facts.values()
            if isinstance(mf, MapFact)
        ]
        column_labels = self.og_df.columns
        return pd.DataFrame(0.0, index=row_labels, columns=column_labels)

    def _select_best_mappings(self, candidates_by_row: Dict[str, List[MatchCandidate]],
                               mapped_df: pd.DataFrame) -> List[MappingResult]:
        """
        Select the best mapping for each row using combined scores.
        
        Uses LLM agents for tie-breaking when:
        - Top 2 candidates are within `llm_ambiguity_threshold` of each other
        - Best candidate score is below `llm_low_confidence_threshold`
        """
        mappings = []
        mapped_facts: Set[str] = set()  # Track which facts are already assigned

        # Sort rows by their best candidate score (highest first) 
        # This ensures high-confidence matches are locked in first
        row_order = sorted(
            candidates_by_row.keys(),
            key=lambda idx: (
                max((c.total_score for c in candidates_by_row[idx]), default=0)
            ),
            reverse=True,
        )

        for row_idx in row_order:
            candidates = candidates_by_row[row_idx]
            if not candidates:
                continue

            # Filter out already-mapped facts
            available = [c for c in candidates if c.map_fact.fact not in mapped_facts]
            if not available:
                continue

            # Re-sort by total_score
            available.sort(key=lambda c: c.total_score, reverse=True)
            
            best = available[0]
            used_llm = False

            # Check if we need LLM tie-breaking
            needs_llm = False
            llm_reason = ""
            if len(available) >= 2:
                gap = best.total_score - available[1].total_score
                if gap < self.config.llm_ambiguity_threshold:
                    needs_llm = True
                    llm_reason = (f"ambiguous: '{best.map_fact.fact}' ({best.total_score:.1f}) vs "
                                  f"'{available[1].map_fact.fact}' ({available[1].total_score:.1f}), gap={gap:.1f}")
            if best.total_score < self.config.llm_low_confidence_threshold:
                needs_llm = True
                llm_reason = f"low confidence: best score {best.total_score:.1f} < threshold {self.config.llm_low_confidence_threshold}"

            if needs_llm:
                if self.config.llm_enabled:
                    logger.info(f"[Pipeline] LLM tie-break needed for '{row_idx}': {llm_reason}")
                else:
                    logger.info(f"[Pipeline] LLM tie-break needed but DISABLED for '{row_idx}': {llm_reason}")

            if needs_llm and self.config.llm_enabled:
                agent = self._get_agent()
                if agent:
                    # Build context for LLM
                    surrounding = self._get_surrounding_rows(row_idx, n=3)
                    temporal_info = None
                    if 'temporal_result' in best.context:
                        tr = best.context['temporal_result']
                        temporal_info = {
                            'matched_years': [(m.year_column, m.hist_filing_year) for m in tr.matches if m.matched],
                            'total_comparisons': tr.total_comparisons,
                        }
                    sum_info = None
                    if 'sum_check' in best.context:
                        sc = best.context['sum_check']
                        sum_info = {
                            'is_sum_row': sc.is_sum_row,
                            'sum_type': sc.sum_type,
                            'component_rows': sc.component_rows[:5],
                        }
                    
                    try:
                        decision = agent.resolve_ambiguous_match(
                            row_idx=row_idx,
                            human_label=self.rows_text.get(row_idx, ''),
                            candidates=available[:3],
                            row_data=self.og_df.loc[row_idx],
                            surrounding_rows=surrounding,
                            temporal_info=temporal_info,
                            sum_check_info=sum_info,
                        )
                        
                        # Apply LLM decision
                        if decision.selected_fact:
                            for c in available:
                                if c.map_fact.fact == decision.selected_fact:
                                    c.llm_score = decision.confidence * 30
                                    best = c
                                    used_llm = True
                                    break
                    except Exception as e:
                        logger.warning(f"LLM tie-breaking failed for '{row_idx}': {e}")

            # Apply the mapping
            fact_name = best.map_fact.fact
            if fact_name in mapped_df.index:
                mapped_df.loc[fact_name] = self.og_df.loc[row_idx]
                mapped_facts.add(fact_name)

                mapping = MappingResult(
                    row_idx=row_idx,
                    fact_name=fact_name,
                    pattern_type=best.pattern_type,
                    total_score=best.total_score,
                    regex_score=best.regex_score,
                    temporal_score=best.temporal_score,
                    summation_score=best.summation_score,
                    llm_score=best.llm_score,
                    confidence=min(1.0, best.total_score / 80.0),
                    used_llm=used_llm,
                    is_total_row=best.is_total_row,
                )
                mappings.append(mapping)

        return mappings
