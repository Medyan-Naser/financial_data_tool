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


