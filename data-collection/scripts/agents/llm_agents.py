"""
LLM AGENTS - Multi-Agent Decision System for Financial Statement Parsing

Uses Ollama (local LLM) via langchain to resolve ambiguous matches:

Agent 1 - THE AUDITOR:
    Receives the top 3 candidates from the regex/logic engine, including their
    context (surrounding rows, temporal scores, summation results).
    Produces a recommendation with reasoning.

Agent 2 - THE FINALIZER:
    Makes the final call based on the Auditor's report. Ensures the 10-year
    trend looks economically rational. Can override or confirm.

Agent 3 - THE DISCOVERER (bonus):
    When a financial item is NOT found but should be present (e.g., Revenue
    for an income statement), this agent examines unmatched rows with their
    CamelCase decompositions and human labels to identify non-standard names.

Usage:
    from agents import AgentOrchestrator
    orchestrator = AgentOrchestrator(model_name="llama3")
    result = orchestrator.resolve_ambiguous_match(candidates, context)
    discovered = orchestrator.discover_missing_items(unmatched_rows, expected_items)
"""

import logging
import json
import os
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ─── LLM File Logger ─────────────────────────────────────────────────────────
# Writes full prompt/response pairs to a JSONL file for review.

_LLM_LOG_DIR = Path(__file__).parent / "logs"
_LLM_LOG_FILE = _LLM_LOG_DIR / "llm_interactions.jsonl"

def _ensure_log_dir():
    _LLM_LOG_DIR.mkdir(parents=True, exist_ok=True)

def log_llm_interaction(
    agent_name: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    response: Optional[str],
    duration_seconds: float,
    error: Optional[str] = None,
    metadata: Optional[Dict] = None,
):
    """Write a full prompt/response record to the JSONL log file."""
    _ensure_log_dir()
    record = {
        "timestamp": datetime.now().isoformat(),
        "agent": agent_name,
        "model": model,
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "response": response,
        "duration_seconds": round(duration_seconds, 2),
        "error": error,
        **(metadata or {}),
    }
    try:
        with open(_LLM_LOG_FILE, "a") as f:
            f.write(json.dumps(record, default=str) + "\n")
    except Exception as e:
        logger.warning(f"Could not write LLM log: {e}")

# Try importing langchain - graceful fallback if not available
try:
    from langchain_ollama import ChatOllama
    from langchain_core.messages import HumanMessage, SystemMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    try:
        from langchain_community.chat_models import ChatOllama
        from langchain_core.messages import HumanMessage, SystemMessage
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        LANGCHAIN_AVAILABLE = False
        logger.warning(
            "langchain/ollama not available. LLM agents will be disabled. "
            "Install with: pip install langchain-ollama langchain-core"
        )


@dataclass
class AgentDecision:
    """Result from an LLM agent."""
    selected_fact: Optional[str]
    confidence: float  # 0.0 to 1.0
    reasoning: str
    agent_name: str
    raw_response: str = ""
    error: Optional[str] = None


@dataclass
class DiscoveryResult:
    """Result from the Discoverer agent."""
    row_idx: str
    suggested_fact: Optional[str]
    confidence: float
    reasoning: str
    raw_response: str = ""


@dataclass
class SumRowValidation:
    """Result from the SumRowValidator agent."""
    row_idx: str
    is_sum_row: bool
    confidence: float
    reasoning: str
    component_rows: List[str] = field(default_factory=list)
    raw_response: str = ""


@dataclass
class DateColumnValidation:
    """Result from the DateColumnValidator agent."""
    selected_columns: List[str]
    confidence: float
    reasoning: str
    rejected_columns: List[str] = field(default_factory=list)
    raw_response: str = ""


@dataclass
class RowClassification:
    """Result from the RowClassifier agent."""
    row_idx: str
    financial_concept: Optional[str]
    is_relevant: bool
    confidence: float
    reasoning: str
    raw_response: str = ""


# ─── Prompt Templates ──────────────────────────────────────────────────────────

AUDITOR_SYSTEM_PROMPT = """You are a Senior Financial Data Auditor specializing in SEC EDGAR filings.
Your job is to analyze candidate matches between raw filing rows and standardized financial concepts.

IMPORTANT RULES:
1. You understand US-GAAP taxonomy deeply. GAAP tags like 'us-gaap_CostOfRevenue' map to 'COGS'.
2. You understand financial statement structure: Revenue → COGS → Gross Profit → OpEx → Operating Income → etc.
3. Numbers matter: if the numerical values don't make economic sense for a concept, it's wrong.
4. Cross-year consistency matters: if a value matched historical filings, that's strong evidence.
5. Summation logic matters: if a row is the sum of rows above it, it's likely a "Total" line item.
6. You MUST respond with valid JSON only. No markdown, no explanations outside JSON.

Respond with exactly this JSON format:
{
    "selected_fact": "the fact name you recommend",
    "confidence": 0.85,
    "reasoning": "brief explanation of why"
}"""

FINALIZER_SYSTEM_PROMPT = """You are a Senior Financial Analyst who makes final decisions on financial data mapping.
You receive an Auditor's recommendation and must confirm or override it.

IMPORTANT RULES:
1. Check if the recommended match makes economic sense over a 10-year trend.
2. Revenue should generally grow or at least not swing wildly without explanation.
3. Net Income can be volatile but should be proportional to Revenue.
4. Balance sheet items should be consistent across years.
5. If the Auditor's pick seems wrong economically, override it.
6. You MUST respond with valid JSON only.

Respond with exactly this JSON format:
{
    "final_fact": "the fact name you confirm or override to",
    "confidence": 0.90,
    "agrees_with_auditor": true,
    "reasoning": "brief explanation"
}"""

DISCOVERER_SYSTEM_PROMPT = """You are a Financial Statement Discovery Agent.
You examine unmatched rows from SEC EDGAR filings to identify financial concepts
that have non-standard names (company-specific taxonomy tags).

IMPORTANT RULES:
1. Companies often use custom tags like 'tsla_DepreciationAmortizationAndImpairment' 
   instead of standard 'us-gaap_DepreciationDepletionAndAmortization'.
2. Use the CamelCase decomposition and human-readable label to identify the concept.
3. Consider the statement type (income, balance, cash flow) for context.
4. Look at numerical values - the magnitude gives hints (billions = revenue-level, 
   millions = expense-level for large companies).
5. You MUST respond with valid JSON only.

Respond with exactly this JSON format:
{
    "suggested_fact": "the standardized fact name this likely represents, or null",
    "confidence": 0.70,
    "reasoning": "brief explanation"
}"""

SUM_ROW_VALIDATOR_PROMPT = """You are a Financial Data Validator specializing in identifying sum/total rows.
Your job is to determine if a row represents a summation of other rows.

IMPORTANT RULES:
1. Sum rows typically have labels like "Total", "Total operating expenses", "Net cash from operating activities".
2. HTML class 'reu' or 'rou' indicates a sum row, but not always reliable.
3. Look at the numerical values - sum rows should approximately equal the sum of component rows.
4. Consider the position in the statement structure.
5. You MUST respond with valid JSON only.

Respond with exactly this JSON format:
{
    "is_sum_row": true,
    "confidence": 0.85,
    "component_rows": ["row1", "row2"],
    "reasoning": "brief explanation"
}"""

DATE_COLUMN_VALIDATOR_PROMPT = """You are a Financial Data Validator specializing in date column selection.
Your job is to identify which columns represent valid fiscal period dates and which should be excluded.

IMPORTANT RULES:
1. Valid date columns are fiscal year-end dates like '2024-09-28', '2023-12-31'.
2. Exclude non-date columns like 'Shares', 'Per Share', ratio columns, or descriptive text.
3. Exclude duplicate date columns or columns with identical data.
4. Financial statements should have 2-4 year comparative periods.
5. You MUST respond with valid JSON only.

Respond with exactly this JSON format:
{
    "selected_columns": ["2024-09-28", "2023-09-30"],
    "rejected_columns": ["Shares", "12 Months Ended"],
    "confidence": 0.90,
    "reasoning": "brief explanation"
}"""

ROW_CLASSIFIER_PROMPT = """You are a Financial Row Classifier.
Your job is to classify unmapped rows to determine if they represent important financial concepts that regex missed.

IMPORTANT RULES:
1. Examine the GAAP tag, human label, and CamelCase decomposition.
2. Determine if this row represents a standard financial concept (Revenue, COGS, etc.).
3. Some rows are metadata, headers, or irrelevant - classify these as not relevant.
4. Consider the magnitude of values (large positive = likely revenue, large negative = likely expense).
5. You MUST respond with valid JSON only.

Respond with exactly this JSON format:
{
    "financial_concept": "Total revenue",
    "is_relevant": true,
    "confidence": 0.75,
    "reasoning": "brief explanation"
}"""


# ─── Agent Implementation ──────────────────────────────────────────────────────

class AgentOrchestrator:
    """
    Orchestrates the multi-agent LLM system for financial statement parsing.
    
    Models:
    - Primary: llama3 (good general reasoning)
    - Fallback: mistral (faster, lighter)
    - Analysis: deepseek-r1 (strong at numerical reasoning) if available
    """

    def __init__(self, model_name: str = "llama3.2",
                 fallback_model: str = "mistral",
                 analysis_model: str = "deepseek-r1",
                 base_url: str = "http://localhost:11434",
                 temperature: float = 0.1,
                 timeout: int = 120):
        """
        Args:
            model_name: Primary Ollama model for Auditor/Finalizer
            fallback_model: Fallback model if primary fails
            analysis_model: Model for numerical analysis (Discoverer)
            base_url: Ollama server URL
            temperature: LLM temperature (low = more deterministic)
            timeout: Request timeout in seconds
        """
        self.model_name = model_name
        self.fallback_model = fallback_model
        self.analysis_model = analysis_model
        self.base_url = base_url
        self.temperature = temperature
        self.timeout = timeout
        self._llm_cache = {}
        self.enabled = LANGCHAIN_AVAILABLE

        if not self.enabled:
            logger.warning("LLM agents disabled - langchain not available")

    def _get_llm(self, model: str):
        """Get or create a ChatOllama instance."""
        if model not in self._llm_cache:
            try:
                self._llm_cache[model] = ChatOllama(
                    model=model,
                    base_url=self.base_url,
                    temperature=self.temperature,
                    timeout=self.timeout,
                    format="json",
                )
            except Exception as e:
                logger.error(f"Failed to create LLM for model '{model}': {e}")
                return None
        return self._llm_cache[model]

    def _invoke_llm(self, system_prompt: str, user_prompt: str,
                    model: Optional[str] = None,
                    agent_name: str = "unknown") -> Optional[str]:
        """
        Invoke an LLM with system + user prompts.
        Falls back to fallback_model if primary fails.
        Logs every call to terminal (INFO) and to the JSONL file.
        """
        if not self.enabled:
            logger.info(f"[Agent:{agent_name}] SKIPPED - LLM agents disabled")
            return None

        model = model or self.model_name
        
        for attempt_model in [model, self.fallback_model]:
            llm = self._get_llm(attempt_model)
            if llm is None:
                continue
            try:
                logger.info(f"[Agent:{agent_name}] Calling model '{attempt_model}'...")
                t0 = time.time()
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ]
                response = llm.invoke(messages)
                duration = time.time() - t0
                content = response.content
                
                # Terminal logging
                logger.info(
                    f"[Agent:{agent_name}] Response received from '{attempt_model}' "
                    f"({duration:.1f}s, {len(content)} chars)"
                )
                
                # File logging - full prompt/response for review
                log_llm_interaction(
                    agent_name=agent_name,
                    model=attempt_model,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    response=content,
                    duration_seconds=duration,
                )
                
                return content
            except Exception as e:
                duration = time.time() - t0 if 't0' in dir() else 0
                logger.warning(f"[Agent:{agent_name}] FAILED with model '{attempt_model}': {e}")
                
                # Log the failure too
                log_llm_interaction(
                    agent_name=agent_name,
                    model=attempt_model,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    response=None,
                    duration_seconds=duration,
                    error=str(e),
                )
                
                if attempt_model == self.fallback_model:
                    logger.error(f"[Agent:{agent_name}] All LLM models failed")
                    return None

        return None

    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """Parse JSON from LLM response, handling common issues."""
        if not response:
            return None
        try:
            # Try direct parse
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            logger.warning(f"Could not parse LLM response as JSON: {response[:200]}")
            return None

    # ─── AUDITOR AGENT ─────────────────────────────────────────────────────

    def run_auditor(self, row_idx: str, human_label: str,
                    candidates: list, row_values: Dict,
                    surrounding_rows: List[Dict],
                    temporal_info: Optional[Dict] = None,
                    sum_check_info: Optional[Dict] = None) -> AgentDecision:
        """
        Agent 1: The Auditor.
        
        Analyzes top candidates and recommends the best match.
        
        Args:
            row_idx: Raw taxonomy tag (e.g., 'us-gaap_CostOfRevenue')
            human_label: Human-readable label from filing
            candidates: Top 3 MatchCandidate objects
            row_values: Dict of {period: value} for this row
            surrounding_rows: List of neighboring rows for context
            temporal_info: Cross-year validation results
            sum_check_info: Summation check results
        """
        if not self.enabled or not candidates:
            logger.info(f"[Agent:Auditor] SKIPPED for '{row_idx}' - agents disabled, using top regex candidate")
            return AgentDecision(
                selected_fact=candidates[0].map_fact.fact if candidates else None,
                confidence=0.5,
                reasoning="LLM agents disabled, using top regex candidate",
                agent_name="Auditor (fallback)",
            )

        logger.info(f"[Agent:Auditor] Analyzing '{row_idx}' (label='{human_label}') with {len(candidates)} candidates")
        for i, c in enumerate(candidates[:3]):
            logger.info(f"[Agent:Auditor]   Candidate {i+1}: '{c.map_fact.fact}' (score={c.regex_score:.1f}, type={c.pattern_type})")

        # Build the prompt with ALL numerical context
        prompt = self._build_auditor_prompt(
            row_idx, human_label, candidates, row_values,
            surrounding_rows, temporal_info, sum_check_info
        )

        response = self._invoke_llm(AUDITOR_SYSTEM_PROMPT, prompt, agent_name="Auditor")
        parsed = self._parse_json_response(response)

        if parsed:
            decision = AgentDecision(
                selected_fact=parsed.get('selected_fact'),
                confidence=float(parsed.get('confidence', 0.5)),
                reasoning=parsed.get('reasoning', ''),
                agent_name="Auditor",
                raw_response=response or "",
            )
            logger.info(f"[Agent:Auditor] Decision: '{decision.selected_fact}' (conf={decision.confidence:.2f}) - {decision.reasoning}")
            return decision

        # Fallback to top candidate
        logger.warning(f"[Agent:Auditor] Failed to parse response for '{row_idx}', falling back to top regex candidate")
        return AgentDecision(
            selected_fact=candidates[0].map_fact.fact if candidates else None,
            confidence=0.4,
            reasoning="Auditor LLM failed, using top regex candidate",
            agent_name="Auditor (error fallback)",
            error=f"LLM response: {response[:200] if response else 'None'}",
        )

    def _build_auditor_prompt(self, row_idx, human_label, candidates,
                               row_values, surrounding_rows,
                               temporal_info, sum_check_info) -> str:
        """Build a detailed prompt for the Auditor agent."""
        lines = [
            f"## Row to Match",
            f"- **Raw GAAP Tag**: `{row_idx}`",
            f"- **Human Label**: `{human_label}`",
            f"- **Values**: {self._format_values(row_values)}",
            "",
            "## Top Candidates (from regex engine):",
        ]

        for i, c in enumerate(candidates[:3]):
            lines.append(f"\n### Candidate {i+1}: `{c.map_fact.fact}`")
            lines.append(f"  - Match type: {c.pattern_type}")
            lines.append(f"  - Regex score: {c.regex_score:.1f}")
            lines.append(f"  - Priority: {c.priority}")
            if c.temporal_score != 0:
                lines.append(f"  - Temporal (cross-year) score: {c.temporal_score:.1f}")
            if c.summation_score != 0:
                lines.append(f"  - Summation score: {c.summation_score:.1f}")
            if c.is_total_row:
                lines.append(f"  - **This row appears to be a TOTAL/SUM row**")

        if surrounding_rows:
            lines.append("\n## Surrounding Rows (context):")
            for sr in surrounding_rows[:5]:
                lines.append(f"  - `{sr.get('idx', '')}` ({sr.get('label', '')}): {sr.get('value', '')}")

        if temporal_info:
            lines.append("\n## Cross-Year Validation:")
            lines.append(f"  - Matched years: {temporal_info.get('matched_years', [])}")
            lines.append(f"  - Total comparisons: {temporal_info.get('total_comparisons', 0)}")

        if sum_check_info:
            lines.append("\n## Summation Check:")
            lines.append(f"  - Is sum row: {sum_check_info.get('is_sum_row', False)}")
            lines.append(f"  - Sum type: {sum_check_info.get('sum_type', 'none')}")
            lines.append(f"  - Components: {sum_check_info.get('component_rows', [])}")

        lines.append("\n## Your Task:")
        lines.append("Select the best candidate. Consider the GAAP tag semantics, ")
        lines.append("numerical values, cross-year consistency, and summation logic.")

        return "\n".join(lines)

    # ─── FINALIZER AGENT ───────────────────────────────────────────────────

    def run_finalizer(self, auditor_decision: AgentDecision,
                      row_idx: str, human_label: str,
                      row_values: Dict,
                      historical_trend: Optional[Dict] = None) -> AgentDecision:
        """
        Agent 2: The Finalizer.
        
        Reviews the Auditor's recommendation and makes the final call.
        Checks if the 10-year trend looks economically rational.
        """
        if not self.enabled:
            logger.info(f"[Agent:Finalizer] SKIPPED for '{row_idx}' - agents disabled, keeping Auditor decision")
            return auditor_decision

        logger.info(
            f"[Agent:Finalizer] Reviewing Auditor decision for '{row_idx}': "
            f"'{auditor_decision.selected_fact}' (conf={auditor_decision.confidence:.2f})"
        )

        prompt = self._build_finalizer_prompt(
            auditor_decision, row_idx, human_label,
            row_values, historical_trend
        )

        response = self._invoke_llm(FINALIZER_SYSTEM_PROMPT, prompt, agent_name="Finalizer")
        parsed = self._parse_json_response(response)

        if parsed:
            final_fact = parsed.get('final_fact', auditor_decision.selected_fact)
            agrees = parsed.get('agrees_with_auditor', True)
            decision = AgentDecision(
                selected_fact=final_fact,
                confidence=float(parsed.get('confidence', auditor_decision.confidence)),
                reasoning=parsed.get('reasoning', ''),
                agent_name="Finalizer",
                raw_response=response or "",
            )
            if agrees:
                logger.info(f"[Agent:Finalizer] CONFIRMED Auditor: '{final_fact}' (conf={decision.confidence:.2f})")
            else:
                logger.info(f"[Agent:Finalizer] OVERRODE Auditor: '{auditor_decision.selected_fact}' -> '{final_fact}' (conf={decision.confidence:.2f})")
            return decision

        # Fallback to auditor's decision
        logger.warning(f"[Agent:Finalizer] Failed to parse response for '{row_idx}', keeping Auditor decision")
        return auditor_decision

    def _build_finalizer_prompt(self, auditor_decision, row_idx, human_label,
                                 row_values, historical_trend) -> str:
        """Build prompt for the Finalizer agent."""
        lines = [
            "## Auditor's Recommendation",
            f"- **Selected Fact**: `{auditor_decision.selected_fact}`",
            f"- **Confidence**: {auditor_decision.confidence:.2f}",
            f"- **Reasoning**: {auditor_decision.reasoning}",
            "",
            f"## Row Details",
            f"- **Raw Tag**: `{row_idx}`",
            f"- **Human Label**: `{human_label}`",
            f"- **Current Values**: {self._format_values(row_values)}",
        ]

        if historical_trend:
            lines.append("\n## 10-Year Historical Trend for this fact:")
            for year, value in sorted(historical_trend.items()):
                lines.append(f"  - {year}: {value:,.0f}" if isinstance(value, (int, float)) else f"  - {year}: {value}")

        lines.append("\n## Your Task:")
        lines.append("Confirm or override the Auditor's recommendation. ")
        lines.append("Check if the values make economic sense for the suggested concept. ")
        lines.append("Revenue should generally be large and positive. Expenses negative. etc.")

        return "\n".join(lines)

