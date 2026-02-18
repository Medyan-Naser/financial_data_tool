"""
HYBRID MATCHER - Candidate-Based Financial Statement Matching

This module implements a sophisticated matching system that returns ranked
candidates for each financial concept. It combines:
1. GAAP tag regex matching
2. Human-readable label matching  
3. IFRS tag matching
4. CamelCase decomposition for non-standard/company-specific tags

Each row in a financial statement gets a list of MatchCandidates, scored
and ranked. The pipeline then uses temporal validation, summation checks,
and optionally LLM agents to make the final selection.

Usage:
    from hybrid_matcher import HybridMatcher
    matcher = HybridMatcher(statement_map)
    candidates = matcher.find_candidates(row_idx, row_data, human_label)
"""

import re
import logging
import pandas as pd
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from statement_maps import MapFact

logger = logging.getLogger(__name__)


@dataclass
class PatternMatch:
    """A single pattern match with metadata."""
    pattern: str
    match_string: str
    pattern_index: int
    match_length: int = 0

    def __post_init__(self):
        self.match_length = len(self.match_string)


@dataclass
class MatchCandidate:
    """
    A potential match between a filing row and a standardized concept.
    
    Attributes:
        map_fact: The MapFact object representing the standardized concept
        pattern_type: 'GAAP', 'IFRS', 'Human', or 'CamelCase'
        matched_patterns: List of PatternMatch objects that triggered this candidate
        priority: Priority from the MapFact (1-10)
        regex_score: Score from regex/pattern quality alone
        temporal_score: Score from cross-year validation (set by temporal_validator)
        summation_score: Score from sum-check verification (set by summation_checker)
        llm_score: Score from LLM agent evaluation (set by llm_agents)
        confidence: Final combined confidence score
        is_total_row: Whether this row was identified as a summation/total
        context: Additional context for LLM agents
    """
    map_fact: MapFact
    pattern_type: str
    matched_patterns: List[PatternMatch]
    priority: int = 5
    regex_score: float = 0.0
    temporal_score: float = 0.0
    summation_score: float = 0.0
    llm_score: float = 0.0
    confidence: float = 0.0
    is_total_row: bool = False
    context: Dict = field(default_factory=dict)

    def __post_init__(self):
        self.priority = self.map_fact.priority

    @property
    def total_score(self) -> float:
        """Combined score from all validation stages."""
        return self.regex_score + self.temporal_score + self.summation_score + self.llm_score

    def __repr__(self):
        return (f"MatchCandidate(fact={self.map_fact.fact}, type={self.pattern_type}, "
                f"regex={self.regex_score:.1f}, temporal={self.temporal_score:.1f}, "
                f"sum={self.summation_score:.1f}, total={self.total_score:.1f})")


