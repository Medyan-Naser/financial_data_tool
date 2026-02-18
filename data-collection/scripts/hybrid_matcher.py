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


# ─── Dimensional row detection ─────────────────────────────────────────────────

# Prefixes added by Filling.py for duplicate row_titles within sections
_DIMENSIONAL_PREFIX_RE = re.compile(r'^(?:D\d+:)+|^[^:]+::', re.IGNORECASE)

def is_dimensional_row(row_idx: str) -> bool:
    """
    Detect SEC HTML dimensional breakdown rows.
    
    These are rows like:
      'Revenue::us-gaap_RevenueFromContract...'   (section prefix)
      'D1:Revenue::us-gaap_RevenueFromContract...' (D1 duplicate prefix)
      'Cost of revenue::us-gaap_CostOfGoods...'    (section prefix)
    
    They represent sub-breakdowns (e.g., product vs service revenue),
    NOT the actual total row. The real total row has no prefix.
    """
    if '::' in row_idx:
        return True
    if row_idx.startswith('D1:') or row_idx.startswith('D2:'):
        return True
    return False


def strip_dimensional_prefix(row_idx: str) -> str:
    """Strip dimensional prefixes to get the underlying GAAP tag."""
    return _DIMENSIONAL_PREFIX_RE.sub('', row_idx)


# ─── Scoring weights ───────────────────────────────────────────────────────────

# Penalty applied to dimensional/prefixed rows so the real total row always wins
DIMENSIONAL_ROW_PENALTY = -50.0

REGEX_SCORING = {
    'pattern_type': {'GAAP': 30, 'IFRS': 20, 'Human': 10, 'CamelCase': 5},
    'pattern_count_bonus': {1: 0, 2: 5, 3: 10, 4: 15},
    'specificity_thresholds': {30: 20, 20: 15, 10: 10, 0: 5},
    'priority_multiplier': 1.0,
    'pattern_position_bonus': {0: 2, 1: 1, 2: 0},
}


# ─── CamelCase decomposition ───────────────────────────────────────────────────

def camel_to_words(tag: str) -> str:
    """
    Convert a CamelCase GAAP tag to space-separated words.
    
    Examples:
        'RevenueFromContractWithCustomerExcludingAssessedTax' 
        -> 'Revenue From Contract With Customer Excluding Assessed Tax'
        
        'CostOfGoodsAndServicesSold' -> 'Cost Of Goods And Services Sold'
    """
    # Remove namespace prefix (us-gaap_, ifrs-full_, ticker_)
    if '_' in tag:
        tag = tag.split('_', 1)[-1]
    
    # Split CamelCase
    words = re.sub(r'([A-Z])', r' \1', tag).strip()
    return words


def decompose_gaap_tag(raw_label: str) -> Dict[str, str]:
    """
    Decompose a raw GAAP label into its components.
    
    Returns:
        Dict with keys: 'namespace', 'tag', 'words', 'is_us_gaap', 'is_custom'
    """
    result = {
        'namespace': '',
        'tag': raw_label,
        'words': '',
        'is_us_gaap': False,
        'is_custom': False,
    }
    
    if '_' in raw_label:
        parts = raw_label.split('_', 1)
        result['namespace'] = parts[0]
        result['tag'] = parts[1]
        result['is_us_gaap'] = parts[0] == 'us-gaap'
        result['is_custom'] = not result['is_us_gaap'] and parts[0] != 'ifrs-full'
    
    result['words'] = camel_to_words(result['tag'])
    return result


# ─── Pattern matching ──────────────────────────────────────────────────────────

def find_pattern_matches(search_string: str, patterns: List[str], pattern_type: str) -> List[PatternMatch]:
    """
    Find all patterns that match the search string.
    
    Args:
        search_string: String to search in
        patterns: List of regex patterns
        pattern_type: 'GAAP', 'IFRS', or 'Human'
    
    Returns:
        List of PatternMatch objects
    """
    matches = []
    if not patterns or not search_string:
        return matches

    for idx, pattern in enumerate(patterns):
        if not pattern:
            continue
        try:
            match = re.search(pattern, search_string, re.IGNORECASE)
            if match:
                matches.append(PatternMatch(
                    pattern=pattern,
                    match_string=match.group(0),
                    pattern_index=idx,
                ))
        except Exception as e:
            logger.error(f"Error matching {pattern_type} pattern '{pattern}': {e}")

    return matches


def compute_regex_score(candidate: MatchCandidate) -> float:
    """
    Compute the regex-based score for a candidate.
    
    Criteria:
    1. Pattern type (GAAP > IFRS > Human > CamelCase)
    2. Number of matched patterns
    3. Specificity (match length)
    4. MapFact priority
    5. Pattern position in list (earlier = more specific)
    """
    config = REGEX_SCORING
    score = 0.0

    # 1. Pattern type
    score += config['pattern_type'].get(candidate.pattern_type, 0)

    # 2. Number of patterns matched
    n = len(candidate.matched_patterns)
    if n >= 4:
        score += config['pattern_count_bonus'][4]
    elif n in config['pattern_count_bonus']:
        score += config['pattern_count_bonus'][n]

    # 3. Specificity (average match length)
    if candidate.matched_patterns:
        avg_len = sum(pm.match_length for pm in candidate.matched_patterns) / n
        for threshold in sorted(config['specificity_thresholds'].keys(), reverse=True):
            if avg_len >= threshold:
                score += config['specificity_thresholds'][threshold]
                break

    # 4. MapFact priority
    score += candidate.priority * config['priority_multiplier']

    # 5. Pattern position
    if candidate.matched_patterns:
        first_idx = min(pm.pattern_index for pm in candidate.matched_patterns)
        score += config['pattern_position_bonus'].get(first_idx, 0)

    return score

