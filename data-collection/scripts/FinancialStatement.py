import pandas as pd
import re
import logging
from typing import List, Dict, Tuple, Optional
from constants import *
from statement_maps import *

logger = logging.getLogger(__name__)


# Scoring configuration for multi-match selection
SCORING_CONFIG = {
    'pattern_type': {
        'GAAP': 30,
        'IFRS': 20,
        'Human': 10
    },
    'pattern_count': {
        1: 0,
        2: 5,
        3: 10,
        4: 15
    },
    'specificity_thresholds': {
        30: 20,
        20: 15,
        10: 10,
        0: 5
    },
    'priority_multiplier': 1,  # Direct use of priority value (1-10)
    'value_magnitude': {
        1_000_000_000: 3,  # 1B+
        100_000_000: 2,    # 100M+
        10_000_000: 1      # 10M+
    },
    'pattern_position': {
        0: 2,  # First pattern
        1: 1,  # Second pattern
        2: 0   # Third+ pattern
    },
    'numeric_similarity': {
        'enabled': True,  # Enable numeric comparison
        'weight': 25,     # High weight for numeric matches
        'tolerance': 0.05  # 5% difference allowed
    },
    'historical_similarity': {
        'enabled': True,   # Enable historical comparison
        'weight': 30,      # Higher weight than current-year comparison
        'tolerance': 0.10  # 10% tolerance for historical data (companies revise numbers)
        # Note: Comparing to 0 will not count as a match (handled in comparison logic)
    }
}


class PatternMatch:
    """Represents a single pattern match with metadata."""
    def __init__(self, pattern: str, match_string: str, pattern_index: int):
        self.pattern = pattern
        self.match_string = match_string  # The actual substring that matched
        self.match_length = len(match_string)
        self.pattern_index = pattern_index  # Position in pattern list


class MatchCandidate:
    """
    Represents a potential match between a row and a MapFact.
    Includes all information needed for scoring.
    """
    def __init__(self, map_fact, pattern_type: str, matched_patterns: List[PatternMatch]):
        self.map_fact = map_fact  # MapFact object
        self.pattern_type = pattern_type  # 'GAAP', 'IFRS', or 'Human'
        self.matched_patterns = matched_patterns  # List of PatternMatch objects
        self.priority = map_fact.priority
        self.score = 0.0  # Calculated score
    
    def __repr__(self):
        return f"MatchCandidate(fact={self.map_fact.fact}, type={self.pattern_type}, score={self.score})"


def calculate_match_score(candidate: MatchCandidate, row_data: pd.Series, 
                          mapped_df: Optional[pd.DataFrame] = None, 
                          statement_obj: Optional['FinancialStatement'] = None) -> float:
    """
    Calculate a score for a match candidate based on multiple criteria.
    
    Args:
        candidate: MatchCandidate object
        row_data: Pandas Series with row values
        mapped_df: DataFrame with already-mapped rows (for numeric comparison)
        statement_obj: FinancialStatement object (for numeric similarity and historical comparison)
    
    Returns:
        Float score (higher is better)
    """
    score = 0.0
    config = SCORING_CONFIG
    
    # Criterion 1: Pattern Type (GAAP > IFRS > Human)
    score += config['pattern_type'].get(candidate.pattern_type, 0)
    
    # Criterion 2: Number of Patterns Matched
    num_patterns = len(candidate.matched_patterns)
    if num_patterns >= 4:
        score += config['pattern_count'][4]
    elif num_patterns in config['pattern_count']:
        score += config['pattern_count'][num_patterns]
    
    # Criterion 3: Pattern Specificity (average match length)
    if candidate.matched_patterns:
        avg_match_length = sum(pm.match_length for pm in candidate.matched_patterns) / num_patterns
        # Find appropriate threshold
        for threshold in sorted(config['specificity_thresholds'].keys(), reverse=True):
            if avg_match_length >= threshold:
                score += config['specificity_thresholds'][threshold]
                break
    
    # Criterion 4: MapFact Priority
    score += candidate.priority * config['priority_multiplier']
    
    # Criterion 5: Row Value Magnitude (detect aggregates)
    try:
        row_sum = abs(row_data.sum())
        for threshold in sorted(config['value_magnitude'].keys(), reverse=True):
            if row_sum > threshold:
                score += config['value_magnitude'][threshold]
                break
    except:
        pass  # If row_data isn't numeric, skip this criterion
    
    # Criterion 6: Pattern Position (earlier patterns slightly preferred)
    if candidate.matched_patterns:
        first_pattern_idx = min(pm.pattern_index for pm in candidate.matched_patterns)
        score += config['pattern_position'].get(first_pattern_idx, 0)
    
    # Criterion 7: Numeric Similarity (NEW - compare values across years)
    if (config['numeric_similarity']['enabled'] and 
        mapped_df is not None and 
        statement_obj is not None and
        candidate.map_fact.fact in mapped_df.index):
        
        # Get the row from mapped_df that would be updated
        existing_row = mapped_df.loc[candidate.map_fact.fact]
        
        # Check if the existing row has any data (might have been pre-matched)
        if (existing_row != 0).any():
            # Compare numeric values
            if statement_obj._rows_numerically_similar(
                row_data, existing_row, 
                tolerance=config['numeric_similarity']['tolerance']):
                # Strong bonus for numeric match
                score += config['numeric_similarity']['weight']
                logger.debug(f"  Numeric match bonus: +{config['numeric_similarity']['weight']}")
    
    # Criterion 8: Historical Data Comparison (NEW - compare against previously parsed statements)
    if (config['historical_similarity']['enabled'] and 
        statement_obj is not None and
        hasattr(statement_obj, 'historical_statements') and
        statement_obj.historical_statements):
        
        historical_match = statement_obj._compare_with_historical(
            candidate.map_fact.fact, 
            row_data,
            tolerance=config['historical_similarity']['tolerance']
        )
        
        if historical_match:
            score += config['historical_similarity']['weight']
            logger.debug(f"  Historical match bonus: +{config['historical_similarity']['weight']} "
                        f"(matched {historical_match['matched_years']} years)")
    
    return score


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
                matched_string = match.group(0)
                matches.append(PatternMatch(pattern, matched_string, idx))
        except Exception as e:
            logger.error(f"Error matching {pattern_type} pattern '{pattern}': {e}")
    
    return matches


class FinancialStatement():
    """
    Base class for financial statements (Income Statement, Balance Sheet, Cash Flow).
    
    Handles:
    - Extracting raw financial data from EDGAR filings
    - Mapping company-specific row labels to standardized terms
    - Tracking rows that are sums/totals
    - Storing calculation relationships from XML
    """

    def __init__(self, og_df: pd.DataFrame, rows_that_are_sum: list, rows_text: dict, cal_facts: dict, sections_dict={}, units_dict=None, historical_statements=None):
        """
        Initialize the financial statement.
        
        Args:
            og_df: Original DataFrame extracted from EDGAR filing
            rows_that_are_sum: List of row indices that represent sum/total rows
            rows_text: Dict mapping row indices to human-readable text
            cal_facts: Calculation relationships from _cal.xml file
            sections_dict: Dict grouping facts by sections in the statement
            units_dict: Dict mapping row indices to UnitInfo objects (unit information)
            historical_statements: Dict of previously parsed statements {year: mapped_df} for disambiguation
        """
        self.og_df = og_df
        self.mapped_df = None
        self.rows_that_are_sum = rows_that_are_sum
        self.rows_text = rows_text
        self.master_list_dict = {}  # Track which rows are sums of other rows
        self.facts_name_dict = {}   # Track renamed facts
        self.special_master_dict = {}
        self.cal_facts = cal_facts
        self.unit = None  # Legacy - replaced by units_dict
        self.units_dict = units_dict or {}  # NEW: Store UnitInfo for each row
        self.sections_dict = sections_dict
        self.mapped_facts = []      # List of successfully mapped facts
        self.mapping_score = {}     # Score for each mapping
        self.historical_statements = historical_statements or {}  # Historical data for disambiguation
        
        # NEW: Raw/unmapped data for debugging
        self.raw_df = None          # All original rows with human-readable labels
        self.raw_columns = []       # List of human-readable column names
        
        # Section indices
        temp_dict = {}
        for key in sections_dict.keys():
            temp_dict[key] = {'start': None, 'end': None}
        self.sections_indxs = temp_dict
        self.facts_mfs = {}         # Map data facts to MapFact objects
        self.found_total_assets = None
    
    def get_mapped_df(self) -> Optional[pd.DataFrame]:
        """
        Get the mapped DataFrame. If mapping hasn't been done, perform it.
        
        Returns:
            Mapped DataFrame or None if mapping failed
        """
        if self.mapped_df is None:
            logger.warning("Mapped DataFrame not yet created. Attempting to map...")
            try:
                self.create_zeroed_df_from_map()
                self.map_facts()
            except Exception as e:
                logger.error(f"Failed to create mapped DataFrame: {e}")
                return None
        return self.mapped_df
    
    def create_zeroed_df_from_map(self):
        """
        Create a zeroed DataFrame based on the statement map.
        Can be overridden by subclasses if needed.
        """
        if not hasattr(self, 'statement_map') or self.statement_map is None:
            logger.error("statement_map not initialized")
            return
        
        map_facts = vars(self.statement_map)
        row_labels = [
            getattr(fact, 'fact') 
            for fact in map_facts.values() 
            if isinstance(fact, MapFact)
        ]
        
        logger.debug(f"Creating mapped DataFrame with {len(row_labels)} standard rows")
        column_labels = self.og_df.columns
        self.mapped_df = pd.DataFrame(0, index=row_labels, columns=column_labels)
        logger.debug(f"Mapped DataFrame shape: {self.mapped_df.shape}")
    
    def map_facts_with_scoring(self):
        """
        Map facts using score-based selection (NEW METHOD).
        
        Strategy:
        1. For each row, find ALL potential matches
        2. Score each match based on multiple criteria
        3. Select the best match
        4. Skip if fact already mapped
        """
        if self.mapped_df is None:
            self.create_zeroed_df_from_map()
        
        # Get all MapFact objects (no need to sort by priority - scoring handles it)
        map_facts = vars(self.statement_map)
        map_fact_items = [(name, mf) for name, mf in map_facts.items() 
                         if isinstance(mf, MapFact)]
        
        mapped_count = 0
        unmapped_rows = []
        
        logger.debug("Starting score-based matching...")
        for idx, row in self.og_df.iterrows():
            if self._is_row_mapped(idx):
                continue
            
            human_string = self.rows_text.get(idx, "")
            
            # Find all potential candidates
            candidates = self._find_all_candidates(idx, row, map_fact_items, human_string)
            
            if not candidates:
                unmapped_rows.append((idx, human_string))
                continue
            
            # Score and select best
            best_match = self._score_and_select_best(candidates, row, idx)
            
            if best_match:
                # Map the row
                fact_row = best_match.map_fact.fact
                self.mapped_df.loc[fact_row] = row
                self.mapped_facts.append((idx, fact_row, best_match.pattern_type))
                self.mapping_score[idx] = best_match.score
                mapped_count += 1
                
                logger.debug(f"Mapped '{idx}' -> '{fact_row}' "
                           f"({best_match.pattern_type}, score: {best_match.score:.1f})")
            else:
                # All candidates already mapped
                unmapped_rows.append((idx, human_string))
        
        logger.info(f"Score-based matching: {mapped_count} out of {len(self.og_df)} rows mapped")
        logger.info(f"Unmapped rows: {len(unmapped_rows)}")
        
        if unmapped_rows and logger.isEnabledFor(logging.DEBUG):
            logger.debug("First 10 unmapped rows:")
            for idx, human_text in unmapped_rows[:10]:
                logger.debug(f"  - {idx}: {human_text}")
    
    def map_facts(self):
        """
        Map facts from original DataFrame to standardized format.
        
        Uses score-based selection by default for better accuracy.
        Set environment variable USE_OLD_MATCHING=1 to use legacy first-match-wins approach.
        
        Strategy (NEW):
        1. For each row, find ALL potential matches
        2. Score each match based on multiple criteria
        3. Select the best match (highest score)
        4. Skip if fact already mapped
        
        Strategy (OLD - deprecated):
        1. Priority-based matching (high-confidence items first)
        2. First match wins (stops immediately)
        """
        import os
        use_old_matching = os.environ.get('USE_OLD_MATCHING', '0') == '1'
        
        if use_old_matching:
            logger.info("Using legacy first-match-wins matching (USE_OLD_MATCHING=1)")
            self._map_facts_legacy()
        else:
            logger.debug("Using score-based matching (default)")
            self.map_facts_with_scoring()
    
    def _map_facts_legacy(self):
        """Legacy first-match-wins approach (for comparison/rollback)."""
        
        if self.mapped_df is None:
            self.create_zeroed_df_from_map()
        
        # Get all MapFact objects sorted by priority (highest first)
        map_facts = vars(self.statement_map)
        map_fact_items = [(name, mf) for name, mf in map_facts.items() 
                         if isinstance(mf, MapFact)]
        map_fact_items.sort(key=lambda x: x[1].priority, reverse=True)
        
        mapped_count = 0
        unmapped_rows = []
        
        # PASS 1: Priority-based matching
        logger.debug("Starting priority-based matching...")
        for idx, row in self.og_df.iterrows():
            if self._is_row_mapped(idx):
                continue
                
            found_match = False
            human_string = self.rows_text.get(idx, "")
            
            for fact_name, map_fact in map_fact_items:
                if found_match:
                    break
                
                # Try GAAP patterns first
                if self._try_pattern_match(idx, row, map_fact, map_fact.gaap_pattern,
                                          human_string, 'GAAP'):
                    mapped_count += 1
                    found_match = True
                    break
                
                # Try IFRS patterns
                if self._try_pattern_match(idx, row, map_fact, map_fact.ifrs_pattern,
                                          human_string, 'IFRS'):
                    mapped_count += 1
                    found_match = True
                    break
                
                # Try human patterns
                if self._try_pattern_match(idx, row, map_fact, map_fact.human_pattern,
                                          human_string, 'Human'):
                    mapped_count += 1
                    found_match = True
                    break
            
            if not found_match:
                unmapped_rows.append((idx, human_string))
        
        logger.info(f"Successfully mapped {mapped_count} out of {len(self.og_df)} rows")
        logger.info(f"Unmapped rows: {len(unmapped_rows)}")
        
        # Log some unmapped rows for debugging
        if unmapped_rows and logger.isEnabledFor(logging.DEBUG):
            logger.debug("First 10 unmapped rows:")
            for idx, human_text in unmapped_rows[:10]:
                logger.debug(f"  - {idx}: {human_text}")
    
    def _is_row_mapped(self, idx):
        """Check if a row has already been mapped."""
        return any(m[0] == idx for m in self.mapped_facts)
    
    def _is_fact_mapped(self, fact_name: str) -> bool:
        """Check if a fact has already been mapped."""
        if self.mapped_df is None:
            return False
        return fact_name in self.mapped_df.index and (self.mapped_df.loc[fact_name] != 0).any()
    
    def _find_all_candidates(self, idx: str, row: pd.Series, map_fact_items: List, human_string: str) -> List[MatchCandidate]:
        """
        Find all potential matches for a row across all MapFacts.
        
        Args:
            idx: Row index (taxonomy name)
            row: Row data
            map_fact_items: List of (name, MapFact) tuples
            human_string: Human-readable label
        
        Returns:
            List of MatchCandidate objects
        """
        candidates = []
        
        for fact_name, map_fact in map_fact_items:
            # Try GAAP patterns
            gaap_matches = find_pattern_matches(idx, map_fact.gaap_pattern, 'GAAP')
            if gaap_matches:
                candidate = MatchCandidate(map_fact, 'GAAP', gaap_matches)
                candidates.append(candidate)
            
            # Try IFRS patterns
            ifrs_matches = find_pattern_matches(idx, map_fact.ifrs_pattern, 'IFRS')
            if ifrs_matches:
                candidate = MatchCandidate(map_fact, 'IFRS', ifrs_matches)
                candidates.append(candidate)
            
            # Try Human patterns
            human_matches = find_pattern_matches(human_string, map_fact.human_pattern, 'Human')
            if human_matches:
                candidate = MatchCandidate(map_fact, 'Human', human_matches)
                candidates.append(candidate)
        
        return candidates
    
    def _score_and_select_best(self, candidates: List[MatchCandidate], row: pd.Series, idx: str) -> Optional[MatchCandidate]:
        """
        Score all candidates and select the best match.
        
        Args:
            candidates: List of MatchCandidate objects
            row: Row data (for value-based scoring)
            idx: Row index (for logging)
        
        Returns:
            Best MatchCandidate or None if no valid match
        """
        if not candidates:
            return None
        
        # Score all candidates (pass mapped_df and self for numeric comparison)
        for candidate in candidates:
            candidate.score = calculate_match_score(candidate, row, 
                                                   mapped_df=self.mapped_df,
                                                   statement_obj=self)
        
        # Sort by score (highest first)
        candidates.sort(key=lambda c: c.score, reverse=True)
        
        # Find first candidate whose fact isn't already mapped
        for candidate in candidates:
            if not self._is_fact_mapped(candidate.map_fact.fact):
                # Log scoring details
                if logger.isEnabledFor(logging.DEBUG) and len(candidates) > 1:
                    logger.debug(f"Row '{idx}' - Selected: {candidate.map_fact.fact} (score: {candidate.score:.1f})")
                    logger.debug(f"  Other candidates: {[(c.map_fact.fact, f'{c.score:.1f}') for c in candidates[1:3]]}")
                return candidate
        
        # All candidates already mapped
        return None
    
    def _try_pattern_match(self, idx, row, map_fact, patterns, human_string, pattern_type):
        """
        Try to match a row against a list of patterns.
        
        Args:
            idx: Row index (GAAP taxonomy name)
            row: Row data
            map_fact: MapFact object
            patterns: List of regex patterns
            human_string: Human-readable label
            pattern_type: 'GAAP', 'IFRS', or 'Human'
        
        Returns:
            True if matched, False otherwise
        """
        if not patterns:
            return False
        
        search_string = human_string if pattern_type == 'Human' else idx
        
        for pattern in patterns:
            try:
                if not pattern:  # Skip empty patterns
                    continue
                    
                if re.search(pattern, search_string, re.IGNORECASE):
                    fact_row = map_fact.fact
                    
                    # Check if this fact is already mapped
                    if (self.mapped_df.loc[fact_row] != 0).any():
                        logger.debug(f"Fact '{fact_row}' already mapped, skipping '{idx}'")
                        return False
                    
                    # Map the row
                    self.mapped_df.loc[fact_row] = row
                    self.mapped_facts.append((idx, fact_row, pattern_type, pattern))
                    logger.debug(f"Mapped '{idx}' -> '{fact_row}' ({pattern_type}: {pattern})")
                    return True
            except Exception as e:
                logger.error(f"Error matching {pattern_type} pattern '{pattern}' for '{idx}': {e}")
        
        return False
    
    def validate_mapped_df(self) -> Dict[str, any]:
        """
        Validate the mapped DataFrame for completeness and accuracy.
        
        Returns:
            Dict with validation results
        """
        if self.mapped_df is None:
            return {'valid': False, 'reason': 'No mapped DataFrame'}
        
        validation = {
            'valid': True,
            'missing_facts': [],
            'zero_rows': [],
            'warnings': []
        }
        
        # Check for rows that are all zeros
        for idx in self.mapped_df.index:
            if (self.mapped_df.loc[idx] == 0).all():
                validation['zero_rows'].append(idx)
        
        if validation['zero_rows']:
            validation['warnings'].append(
                f"Found {len(validation['zero_rows'])} rows with all zeros"
            )
        
        return validation
    
    def create_raw_statement(self, skip_logging=True):
        """
        Create raw statement with ALL original rows using human-readable labels.
        Handles duplicate labels by comparing numeric values.
        
        Args:
            skip_logging: If True, don't log these rows to pattern_log (default True)
        
        Creates:
            self.raw_df: DataFrame with all original rows (unique indices)
            self.raw_columns: List of human-readable labels for each row
        """
        if self.og_df is None or self.og_df.empty:
            logger.warning("No original data available for raw statement")
            return
        
        # Build mapping: human_label -> list of (taxonomy_id, row_data)
        label_to_rows = {}
        for idx in self.og_df.index:
            human_label = self.rows_text.get(idx, idx)
            row_data = self.og_df.loc[idx]
            
            if human_label not in label_to_rows:
                label_to_rows[human_label] = []
            label_to_rows[human_label].append((idx, row_data))
        
        # Process each label group
        raw_data_dict = {}  # final_label -> row_data
        
        for human_label, rows in label_to_rows.items():
            if len(rows) == 1:
                # Single row with this label - use as-is
                final_label = human_label
                raw_data_dict[final_label] = rows[0][1]
            else:
                # Multiple rows with same label - need to decide how to handle
                logger.debug(f"Duplicate label '{human_label}' found {len(rows)} times")
                
                # Group rows by numeric similarity
                merged_groups = self._group_rows_by_numeric_similarity(rows)
                
                # Create unique labels for each group
                if len(merged_groups) == 1:
                    # All rows are numerically similar - merge into one
                    final_label = human_label
                    raw_data_dict[final_label] = merged_groups[0]['merged_data']
                else:
                    # Different numeric values - add suffixes
                    for idx, group in enumerate(merged_groups):
                        if idx == 0:
                            final_label = human_label
                        else:
                            final_label = f"{human_label} ({idx + 1})"
                        raw_data_dict[final_label] = group['merged_data']
        
        # Create DataFrame from processed data
        self.raw_df = pd.DataFrame(raw_data_dict).T
        self.raw_columns = list(raw_data_dict.keys())
        
        logger.info(f"Created raw statement with {len(self.raw_df)} rows "
                   f"(from {len(self.og_df)} original rows)")
    
    def _group_rows_by_numeric_similarity(self, rows, tolerance=0.05):
        """
        Group rows that have similar numeric values across columns.
        
        Args:
            rows: List of (taxonomy_id, row_data) tuples
            tolerance: Percentage difference allowed (0.05 = 5%)
        
        Returns:
            List of groups, each containing merged data
        """
        groups = []
        
        for taxonomy_id, row_data in rows:
            # Try to find a matching group
            matched_group = None
            
            for group in groups:
                if self._rows_numerically_similar(row_data, group['merged_data'], tolerance):
                    matched_group = group
                    break
            
            if matched_group:
                # Add to existing group (take first non-zero value)
                for col in row_data.index:
                    if matched_group['merged_data'][col] == 0 and row_data[col] != 0:
                        matched_group['merged_data'][col] = row_data[col]
                matched_group['members'].append(taxonomy_id)
            else:
                # Create new group
                groups.append({
                    'merged_data': row_data.copy(),
                    'members': [taxonomy_id]
                })
        
        return groups
    
    def _rows_numerically_similar(self, row1: pd.Series, row2: pd.Series, tolerance=0.05) -> bool:
        """
        Check if two rows are numerically similar across common columns.
        
        Args:
            row1, row2: Pandas Series with numeric data
            tolerance: Percentage difference allowed (0.05 = 5%)
        
        Returns:
            True if rows are similar, False otherwise
        """
        # Get common columns
        common_cols = row1.index.intersection(row2.index)
        
        if len(common_cols) == 0:
            return False  # No common columns to compare
        
        matches = 0
        comparisons = 0
        
        for col in common_cols:
            val1 = row1[col]
            val2 = row2[col]
            
            # Skip if both are NaN
            if pd.isna(val1) and pd.isna(val2):
                continue
            
            # Skip if one is NaN and other is 0 (common case)
            if (pd.isna(val1) and val2 == 0) or (pd.isna(val2) and val1 == 0):
                continue
            
            comparisons += 1
            
            # Both are zero - don't count as match (can't distinguish)
            if val1 == 0 and val2 == 0:
                continue
            
            # One is zero, other isn't - not a match
            if val1 == 0 or val2 == 0:
                return False
            
            # Calculate percentage difference
            avg = (abs(val1) + abs(val2)) / 2
            diff = abs(val1 - val2)
            pct_diff = diff / avg if avg != 0 else 0
            
            if pct_diff <= tolerance:
                matches += 1
            else:
                return False  # Any significant difference = not a match
        
        # Need at least 2 non-zero comparisons to be confident
        if comparisons < 2:
            return False
        
        # All compared values matched
        return matches >= comparisons * 0.8  # 80% of values must match
    
    def _compare_with_historical(self, fact_name: str, current_row: pd.Series, tolerance=0.10) -> Optional[dict]:
        """
        Compare current row values against historical statements for the same fact.
        
        This helps disambiguate when multiple rows match the same pattern by checking
        which candidate's values match previously parsed historical data.
        
        Args:
            fact_name: Name of the fact to compare (e.g., "Total revenue")
            current_row: Series with current year's data including overlapping years
            tolerance: Percentage difference allowed for historical comparison (default 10%)
        
        Returns:
            Dict with match info if found, None otherwise
            {
                'matched': True/False,
                'matched_years': List of years that matched,
                'total_comparisons': Number of comparisons made
            }
        """
        if not self.historical_statements:
            return None
        
        # Get columns from current row (these are years/periods)
        current_columns = current_row.index.tolist()
        
        matched_years = []
        total_comparisons = 0
        
        # For each historical statement
        for hist_year, hist_df in self.historical_statements.items():
            # Check if this fact exists in historical data
            if fact_name not in hist_df.index:
                continue
            
            hist_row = hist_df.loc[fact_name]
            
            # Find overlapping columns (years that exist in both current and historical)
            common_cols = [col for col in current_columns if col in hist_row.index]
            
            if not common_cols:
                continue
            
            # Compare values in common columns
            for col in common_cols:
                curr_val = current_row[col]
                hist_val = hist_row[col]
                
                # Skip NaN comparisons
                if pd.isna(curr_val) or pd.isna(hist_val):
                    continue
                
                total_comparisons += 1
                
                # IMPORTANT: Don't count zero==zero as a match (as per user requirement)
                if curr_val == 0 and hist_val == 0:
                    continue
                
                # If one is zero and other isn't, not a match
                if curr_val == 0 or hist_val == 0:
                    continue
                
                # Calculate percentage difference
                avg = (abs(curr_val) + abs(hist_val)) / 2
                diff = abs(curr_val - hist_val)
                pct_diff = diff / avg if avg != 0 else 0
                
                if pct_diff <= tolerance:
                    matched_years.append((hist_year, col))
                    logger.debug(f"    Historical match: {fact_name} {col}: "
                               f"current={curr_val:,.0f} vs hist({hist_year})={hist_val:,.0f} "
                               f"(diff={pct_diff*100:.1f}%)")
        
        # Return match info if we had successful comparisons
        if matched_years:
            return {
                'matched': True,
                'matched_years': matched_years,
                'total_comparisons': total_comparisons
            }
        
        return None

class IncomeStatement(FinancialStatement):
    """
    Income Statement processor.
    
    Maps company-specific income statement items to standardized format:
    - Revenue, COGS, Gross Profit
    - Operating expenses (SG&A, R&D, D&A)
    - Operating Income
    - Non-operating items
    - Net Income, EPS
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.statement_map = IncomeStatementMap()
        # Create raw statement for debugging
        self.create_raw_statement()

    def map_facts(self):
        """
        Map income statement facts. Uses parent class implementation and adds validation.
        """
        super().map_facts()
        # Validate key facts after mapping
        self._validate_key_facts()
    
    def _validate_key_facts(self):
        """
        Validate that key income statement facts are present.
        """
        key_facts = [TotalRevenue, NetIncome]
        missing = []
        
        for fact in key_facts:
            if fact in self.mapped_df.index:
                if (self.mapped_df.loc[fact] == 0).all():
                    missing.append(fact)
            else:
                missing.append(fact)
        
        if missing:
            logger.warning(f"Missing key income statement facts: {missing}")
        
    

class BalanceSheet(FinancialStatement):
    """
    Balance Sheet processor.
    
    Maps company-specific balance sheet items to standardized format:
    - Assets (Current, Non-Current, Total)
    - Liabilities (Current, Non-Current, Total)
    - Equity
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from statement_maps import BalanceSheetMap
        self.statement_map = BalanceSheetMap()
        # Create raw statement for debugging
        self.create_raw_statement()
    
    def create_zeroed_df_from_map(self):
        """
        Create a DataFrame with standardized balance sheet row labels.
        """
        map_facts = vars(self.statement_map)
        row_labels = [
            getattr(fact, 'fact') 
            for fact in map_facts.values() 
            if isinstance(fact, MapFact)
        ]
        
        logger.debug(f"Creating mapped DataFrame with {len(row_labels)} standard rows")
        column_labels = self.og_df.columns
        self.mapped_df = pd.DataFrame(0, index=row_labels, columns=column_labels)
        logger.debug(f"Mapped DataFrame shape: {self.mapped_df.shape}")
    
    def map_facts(self):
        """
        Map balance sheet facts using the same multi-pass strategy as income statement.
        """
        # Use the parent class mapping logic
        super().map_facts()
    
    def _validate_key_facts(self):
        """
        Validate that key balance sheet facts are present.
        """
        key_facts = [TotalAssets, TotalLiabilities, StockholdersEquity]
        missing = []
        
        for fact in key_facts:
            if fact in self.mapped_df.index:
                if (self.mapped_df.loc[fact] == 0).all():
                    missing.append(fact)
            else:
                missing.append(fact)
        
        if missing:
            logger.warning(f"Missing key balance sheet facts: {missing}")


class CashFlow(FinancialStatement):
    """
    Cash Flow Statement processor.
    
    Maps company-specific cash flow items to standardized format:
    - Operating Activities
    - Investing Activities
    - Financing Activities
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from statement_maps import CashFlowMap
        self.statement_map = CashFlowMap()
        # Create raw statement for debugging
        self.create_raw_statement()
    
    def create_zeroed_df_from_map(self):
        """
        Create a DataFrame with standardized cash flow row labels.
        """
        map_facts = vars(self.statement_map)
        row_labels = [
            getattr(fact, 'fact') 
            for fact in map_facts.values() 
            if isinstance(fact, MapFact)
        ]
        
        logger.debug(f"Creating mapped DataFrame with {len(row_labels)} standard rows")
        column_labels = self.og_df.columns
        self.mapped_df = pd.DataFrame(0, index=row_labels, columns=column_labels)
        logger.debug(f"Mapped DataFrame shape: {self.mapped_df.shape}")
    
    def map_facts(self):
        """
        Map cash flow facts using the same multi-pass strategy.
        """
        # Use the parent class mapping logic
        super().map_facts()
    
    def _validate_key_facts(self):
        """
        Validate that key cash flow facts are present.
        """
        key_facts = ["Net cash from operating activities", "Net cash from investing activities", 
                    "Net cash from financing activities"]
        missing = []
        
        for fact in key_facts:
            if fact in self.mapped_df.index:
                if (self.mapped_df.loc[fact] == 0).all():
                    missing.append(fact)
            else:
                missing.append(fact)
        
        if missing:
            logger.warning(f"Missing key cash flow facts: {missing}")