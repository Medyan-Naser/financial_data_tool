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
