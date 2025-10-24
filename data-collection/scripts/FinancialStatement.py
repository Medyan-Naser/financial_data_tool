import pandas as pd
import re
import logging
from typing import List, Dict, Tuple, Optional
from constants import *
from statement_maps import *

logger = logging.getLogger(__name__)


class FinancialStatement():
    """
    Base class for financial statements (Income Statement, Balance Sheet, Cash Flow).
    
    Handles:
    - Extracting raw financial data from EDGAR filings
    - Mapping company-specific row labels to standardized terms
    - Tracking rows that are sums/totals
    - Storing calculation relationships from XML
    """

    def __init__(self, og_df: pd.DataFrame, rows_that_are_sum: list, rows_text: dict, cal_facts: dict, sections_dict={}):
        """
        Initialize the financial statement.
        
        Args:
            og_df: Original DataFrame extracted from EDGAR filing
            rows_that_are_sum: List of row indices that represent sum/total rows
            rows_text: Dict mapping row indices to human-readable text
            cal_facts: Calculation relationships from _cal.xml file
            sections_dict: Dict grouping facts by sections in the statement
        """
        self.og_df = og_df
        self.mapped_df = None
        self.rows_that_are_sum = rows_that_are_sum
        self.rows_text = rows_text
        self.master_list_dict = {}  # Track which rows are sums of other rows
        self.facts_name_dict = {}   # Track renamed facts
        self.special_master_dict = {}
        self.cal_facts = cal_facts
        self.unit = None
        self.sections_dict = sections_dict
        self.mapped_facts = []      # List of successfully mapped facts
        self.mapping_score = {}     # Score for each mapping
        
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
    
    def map_facts(self):
        """
        Map facts from original DataFrame to standardized format.
        
        Multi-pass strategy:
        1. Priority-based matching (high-confidence items first)
        2. GAAP taxonomy matching
        3. IFRS taxonomy matching (for international companies)
        4. Human-readable label matching
        5. Report results and unmapped items
        
        Can be overridden by subclasses if needed.
        """
        if not hasattr(self, 'statement_map') or self.statement_map is None:
            logger.error("statement_map not initialized")
            return
        
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