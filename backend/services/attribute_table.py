"""
Attribute table view with editing, filtering, and lazy loading for large datasets.
Implements pagination and efficient data handling.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import threading
import queue

logger = logging.getLogger(__name__)


@dataclass
class TableConfig:
    """Configuration for attribute table"""
    page_size: int = 100
    enable_editing: bool = True
    enable_sorting: bool = True
    enable_filtering: bool = True
    cache_size: int = 5  # Number of pages to cache
    lazy_load: bool = True


class AttributeTable:
    """Efficient attribute table with lazy loading and editing"""
    
    def __init__(self, layer_name: str, data_source: Any, config: Optional[TableConfig] = None):
        self.layer_name = layer_name
        self.data_source = data_source
        self.config = config or TableConfig()
        
        # Data storage
        self._data = None
        self._total_records = 0
        self._columns = []
        
        # Caching
        self._page_cache: Dict[int, List[Dict]] = {}
        self._sorted_indices = None
        self._filtered_indices = None
        
        # State
        self._sort_field = None
        self._sort_ascending = True
        self._current_filters: List[Tuple[str, str, Any]] = []
        self._current_page = 0
        
        # Threading
        self._load_queue = queue.Queue()
        self._load_thread = None
        self._stop_loading = False
        
        # Load initial data
        self._load_data()
    
    def _load_data(self):
        """Load data from source"""
        try:
            if hasattr(self.data_source, 'read'):
                # GeoPandas GeoDataFrame
                self._data = self.data_source
                self._columns = list(self._data.columns)
                self._total_records = len(self._data)
            elif isinstance(self.data_source, list):
                # List of dicts
                self._data = self.data_source
                if self._data:
                    self._columns = list(self._data[0].keys())
                self._total_records = len(self._data)
            
            self._sorted_indices = list(range(self._total_records))
            logger.info(f"Loaded {self._total_records} records from {self.layer_name}")
        except Exception as e:
            logger.error(f"Failed to load attribute data: {e}")
            self._data = []
            self._total_records = 0
    
    def get_columns(self) -> List[str]:
        """Get column names"""
        return self._columns.copy()
    
    def get_row_count(self) -> int:
        """Get total number of rows (after filtering)"""
        if self._filtered_indices is not None:
            return len(self._filtered_indices)
        return self._total_records
    
    def get_page_count(self) -> int:
        """Get total number of pages"""
        return (self.get_row_count() + self.config.page_size - 1) // self.config.page_size
    
    def get_page(self, page_num: int = 0) -> List[Dict[str, Any]]:
        """Get page of records (lazy loaded)"""
        if self.config.lazy_load:
            return self._get_page_lazy(page_num)
        else:
            return self._get_page_direct(page_num)
    
    def _get_page_direct(self, page_num: int) -> List[Dict[str, Any]]:
        """Get page directly without caching"""
        if page_num < 0 or page_num >= self.get_page_count():
            return []
        
        # Get indices for this page
        indices = self._get_page_indices(page_num)
        
        # Fetch data
        rows = []
        for idx in indices:
            row = self._get_record(idx)
            if row:
                rows.append(row)
        
        return rows
    
    def _get_page_lazy(self, page_num: int) -> List[Dict[str, Any]]:
        """Get page with caching"""
        # Check cache
        if page_num in self._page_cache:
            return self._page_cache[page_num]
        
        # Load page
        page_data = self._get_page_direct(page_num)
        
        # Cache management
        if len(self._page_cache) >= self.config.cache_size:
            # Remove oldest page
            oldest_page = min(self._page_cache.keys())
            del self._page_cache[oldest_page]
        
        self._page_cache[page_num] = page_data
        return page_data
    
    def _get_page_indices(self, page_num: int) -> List[int]:
        """Get row indices for page"""
        indices = self._filtered_indices if self._filtered_indices is not None else self._sorted_indices
        if indices is None:
            return []
        
        start = page_num * self.config.page_size
        end = start + self.config.page_size
        
        if isinstance(indices, list):
            return indices[start:end]
        return list(indices[start:end])
    
    def _get_record(self, index: int) -> Optional[Dict[str, Any]]:
        """Get single record by index"""
        try:
            if self._data is None:
                return None
            
            if not isinstance(self._data, list) and hasattr(self._data, 'iloc'):
                # GeoPandas DataFrame
                return dict(self._data.iloc[index])
            elif isinstance(self._data, list):
                return self._data[index]
        except Exception as e:
            logger.error(f"Failed to get record: {e}")
        
        return None
    
    def sort(self, field: str, ascending: bool = True):
        """Sort table by field"""
        if field not in self._columns:
            logger.error(f"Invalid sort field: {field}")
            return
        
        self._sort_field = field
        self._sort_ascending = ascending
        
        try:
            # Get values for sorting
            values = []
            for i in range(self._total_records):
                record = self._get_record(i)
                if record:
                    values.append((i, record.get(field)))
            
            # Sort
            values.sort(key=lambda x: (x[1] is None, x[1]), reverse=not ascending)
            self._sorted_indices = [idx for idx, _ in values]
            
            # Clear cache
            self._page_cache.clear()
            self._current_page = 0
            
            logger.info(f"Sorted by {field} ({ascending and 'ASC' or 'DESC'})")
        except Exception as e:
            logger.error(f"Sort failed: {e}")
    
    def add_filter(self, field: str, operator: str, value: Any):
        """Add filter condition"""
        if field not in self._columns:
            logger.error(f"Invalid filter field: {field}")
            return
        
        self._current_filters.append((field, operator, value))
        self._apply_filters()
    
    def clear_filters(self):
        """Clear all filters"""
        self._current_filters.clear()
        self._filtered_indices = None
        self._page_cache.clear()
        self._current_page = 0
    
    def _apply_filters(self):
        """Apply current filters to create filtered indices"""
        if not self._current_filters:
            self._filtered_indices = None
            return
        
        filtered = []
        
        for i in range(self._total_records):
            record = self._get_record(i)
            if not record:
                continue
            
            # Check all filters
            matches_all = True
            for field, operator, value in self._current_filters:
                if not self._check_filter(record.get(field), operator, value):
                    matches_all = False
                    break
            
            if matches_all:
                filtered.append(i)
        
        self._filtered_indices = filtered
        self._page_cache.clear()
        self._current_page = 0
    
    def _check_filter(self, record_value: Any, operator: str, filter_value: Any) -> bool:
        """Check if record value matches filter"""
        try:
            if operator == "=":
                return record_value == filter_value
            elif operator == "!=":
                return record_value != filter_value
            elif operator == "<":
                return float(record_value) < float(filter_value)
            elif operator == "<=":
                return float(record_value) <= float(filter_value)
            elif operator == ">":
                return float(record_value) > float(filter_value)
            elif operator == ">=":
                return float(record_value) >= float(filter_value)
            elif operator == "contains":
                return str(filter_value).lower() in str(record_value).lower()
            elif operator == "starts_with":
                return str(record_value).lower().startswith(str(filter_value).lower())
            elif operator == "ends_with":
                return str(record_value).lower().endswith(str(filter_value).lower())
            else:
                return True
        except (ValueError, TypeError):
            return False
    
    def get_record(self, row_index: int) -> Optional[Dict[str, Any]]:
        """Get specific record (with filtering applied)"""
        indices = self._filtered_indices if self._filtered_indices is not None else self._sorted_indices
        if indices is None or row_index < 0 or row_index >= len(indices):
            return None
        
        return self._get_record(indices[row_index])
    
    def update_record(self, row_index: int, updates: Dict[str, Any]) -> bool:
        """Update record (if editing enabled)"""
        if not self.config.enable_editing:
            logger.warning("Editing is disabled")
            return False
        
        indices = self._filtered_indices if self._filtered_indices is not None else self._sorted_indices
        if indices is None or row_index < 0 or row_index >= len(indices):
            return False
        
        try:
            actual_index = indices[row_index]
            record = self._get_record(actual_index)
            
            if record:
                for key, value in updates.items():
                    if key in record:
                        record[key] = value
                
                # Clear cache
                self._page_cache.clear()
                
                logger.info(f"Updated record {actual_index}")
                return True
        except Exception as e:
            logger.error(f"Update failed: {e}")
        
        return False
    
    def delete_record(self, row_index: int) -> bool:
        """Delete record"""
        if not self.config.enable_editing:
            logger.warning("Editing is disabled")
            return False
        
        indices = self._filtered_indices if self._filtered_indices is not None else self._sorted_indices
        if indices is None or row_index < 0 or row_index >= len(indices):
            return False
        
        try:
            actual_index = indices[row_index]
            
            if self._data is None:
                return False
            
            if not isinstance(self._data, list) and hasattr(self._data, 'drop') and hasattr(self._data, 'index'):
                # GeoPandas DataFrame
                self._data = self._data.drop(self._data.index[actual_index])
            elif isinstance(self._data, list):
                del self._data[actual_index]
            
            self._total_records -= 1
            self._sorted_indices = list(range(self._total_records))
            self._page_cache.clear()
            
            logger.info(f"Deleted record {actual_index}")
            return True
        except Exception as e:
            logger.error(f"Delete failed: {e}")
        
        return False
    
    def get_statistics(self, field: str) -> Dict[str, Any]:
        """Get statistics for numeric field"""
        import numpy as np
        
        if field not in self._columns:
            return {}
        
        values = []
        indices = self._filtered_indices or range(self._total_records)
        
        for i in indices:
            record = self._get_record(i)
            if record:
                try:
                    values.append(float(record.get(field, 0)))
                except (ValueError, TypeError):
                    pass
        
        if not values:
            return {}
        
        values_array = np.array(values)
        
        return {
            'count': len(values),
            'min': float(values_array.min()),
            'max': float(values_array.max()),
            'mean': float(values_array.mean()),
            'median': float(np.median(values_array)),
            'std_dev': float(values_array.std()),
            'sum': float(values_array.sum())
        }
    
    def export_to_dict_list(self) -> List[Dict[str, Any]]:
        """Export all records as list of dicts"""
        records = []
        indices = self._filtered_indices or range(self._total_records)
        
        for i in indices:
            record = self._get_record(i)
            if record:
                records.append(record)
        
        return records
