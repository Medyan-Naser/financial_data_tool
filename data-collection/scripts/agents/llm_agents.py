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

\
