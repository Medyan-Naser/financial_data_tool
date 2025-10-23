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
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement create_zeroed_df_from_map")
    
    def map_facts(self):
        """
        Map facts from original DataFrame to standardized format.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement map_facts")
    
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
    
    def create_zeroed_df_from_map(self):
        """
        Create a DataFrame with standardized row labels, initialized to zero.
        """
        # Extract row labels from the MapFact attributes
        map_facts = vars(self.statement_map)
        row_labels = [
            getattr(fact, 'fact') 
            for fact in map_facts.values() 
            if isinstance(fact, MapFact)
        ]
        
        logger.debug(f"Creating mapped DataFrame with {len(row_labels)} standard rows")
        
        # Get column headers (dates) from original DataFrame
        column_labels = self.og_df.columns
        
        # Create zeroed DataFrame
        self.mapped_df = pd.DataFrame(0, index=row_labels, columns=column_labels)
        logger.debug(f"Mapped DataFrame shape: {self.mapped_df.shape}")

    def map_facts(self):
        """
        Map facts from original DataFrame to standardized format.
        
        Uses regex patterns to match:
        1. GAAP taxonomy names (e.g., us-gaap_Revenue)
        2. Human-readable labels from the filing
        """
        if self.mapped_df is None:
            self.create_zeroed_df_from_map()
        
        map_facts = vars(self.statement_map)
        mapped_count = 0
        
        # Iterate through each row in the original dataframe
        for idx, row in self.og_df.iterrows():
            found_match = False
            
            # Extract the human-readable text for this row
            human_string = self.rows_text.get(idx, "")
            
            # Try to match against each MapFact
            for fact_name, map_fact in map_facts.items():
                if found_match:
                    break
                    
                if not isinstance(map_fact, MapFact):
                    continue
                
                # Try GAAP pattern matching first (more reliable)
                for pattern in map_fact.gaap_pattern:
                    try:
                        if re.search(pattern, idx, re.IGNORECASE):
                            fact_row = map_fact.fact
                            
                            # Check if this fact is already mapped
                            if (self.mapped_df.loc[fact_row] != 0).any():
                                logger.debug(f"Fact '{fact_row}' already mapped, skipping '{idx}'")
                                continue
                            
                            self.mapped_df.loc[fact_row] = row
                            self.mapped_facts.append((idx, fact_row, 'gaap', pattern))
                            logger.debug(f"Mapped '{idx}' -> '{fact_row}' (GAAP: {pattern})")
                            mapped_count += 1
                            found_match = True
                            break
                    except Exception as e:
                        logger.error(f"Error matching GAAP pattern '{pattern}' for '{idx}': {e}")
                
                if found_match:
                    continue
                
                # Try human pattern matching
                for pattern in map_fact.human_pattern:
                    try:
                        if re.search(pattern, human_string, re.IGNORECASE):
                            fact_row = map_fact.fact
                            
                            # Check if this fact is already mapped
                            if (self.mapped_df.loc[fact_row] != 0).any():
                                logger.debug(f"Fact '{fact_row}' already mapped, skipping '{idx}'")
                                continue
                            
                            self.mapped_df.loc[fact_row] = row
                            self.mapped_facts.append((idx, fact_row, 'human', pattern))
                            logger.debug(f"Mapped '{idx}' -> '{fact_row}' (Human: {pattern})")
                            mapped_count += 1
                            found_match = True
                            break
                    except Exception as e:
                        logger.error(f"Error matching human pattern '{pattern}' for '{idx}': {e}")
        
        logger.info(f"Successfully mapped {mapped_count} out of {len(self.og_df)} rows")
        
        # Validate key facts are present
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
        # TODO: Create BalanceSheetMap similar to IncomeStatementMap
        self.statement_map = None
    
    def create_zeroed_df_from_map(self):
        """
        Create a DataFrame with standardized balance sheet row labels.
        """
        # For now, just copy the original DataFrame
        # TODO: Implement proper mapping when BalanceSheetMap is created
        logger.warning("Balance sheet mapping not yet implemented")
        self.mapped_df = self.og_df.copy()
    
    def map_facts(self):
        """
        Map balance sheet facts.
        """
        # TODO: Implement balance sheet mapping
        logger.warning("Balance sheet mapping not yet implemented")
        pass


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
        # TODO: Create CashFlowMap similar to IncomeStatementMap
        self.statement_map = None
    
    def create_zeroed_df_from_map(self):
        """
        Create a DataFrame with standardized cash flow row labels.
        """
        # For now, just copy the original DataFrame
        # TODO: Implement proper mapping when CashFlowMap is created
        logger.warning("Cash flow mapping not yet implemented")
        self.mapped_df = self.og_df.copy()
    
    def map_facts(self):
        """
        Map cash flow facts.
        """
        # TODO: Implement cash flow mapping
        logger.warning("Cash flow mapping not yet implemented")
        pass