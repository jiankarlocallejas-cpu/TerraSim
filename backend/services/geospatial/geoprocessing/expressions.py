"""
Advanced Expression Engine and Field Calculator.
Support for custom field expressions and complex attribute calculations.

Features:
- Custom expression evaluator
- Field calculations with multiple data types
- Conditional expressions
- String manipulation
- Date/time functions
- Aggregate functions
"""

import logging
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass
import re
from datetime import datetime
import numpy as np
import pandas as pd
from geopandas import GeoDataFrame
import operator

logger = logging.getLogger(__name__)


class ExpressionFunction:
    """Built-in expression function."""
    
    def __init__(self, name: str, func: Callable, arg_count: int = -1):
        self.name = name
        self.func = func
        self.arg_count = arg_count  # -1 for variable args
    
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


class FieldExpressionContext:
    """Context for field expression evaluation."""
    
    def __init__(self, gdf: GeoDataFrame, row_index: Optional[int] = None):
        self.gdf = gdf
        self.row_index = row_index
        self.current_row = gdf.iloc[row_index] if row_index is not None else None
        self.variables: Dict[str, Any] = {}
    
    def get_field_value(self, field_name: str) -> Any:
        """Get field value for current row."""
        if self.current_row is None:
            return None
        if field_name in self.current_row:
            return self.current_row[field_name]
        return None


class FieldCalculator:
    """
    Advanced field calculator for attribute operations.
    Supports complex expressions on GeoDataFrames.
    """
    
    def __init__(self):
        self.functions = self._register_functions()
    
    def _register_functions(self) -> Dict[str, Callable]:
        """Register built-in functions."""
        return {
            # Math functions
            'abs': abs,
            'round': round,
            'sqrt': np.sqrt,
            'sin': np.sin,
            'cos': np.cos,
            'tan': np.tan,
            'exp': np.exp,
            'log': np.log,
            'log10': np.log10,
            'ceil': np.ceil,
            'floor': np.floor,
            'min': min,
            'max': max,
            'sum': sum,
            'avg': lambda *args: sum(args) / len(args) if args else 0,
            'pow': pow,
            
            # String functions
            'upper': str.upper,
            'lower': str.lower,
            'len': len,
            'substr': lambda s, start, end: s[start:end],
            'concat': lambda *args: ''.join(str(a) for a in args),
            'replace': str.replace,
            'trim': str.strip,
            'lpad': lambda s, n, c=' ': str(s).rjust(n, c),
            'rpad': lambda s, n, c=' ': str(s).ljust(n, c),
            
            # Date/time functions
            'now': datetime.now,
            'year': lambda d: d.year if isinstance(d, datetime) else None,
            'month': lambda d: d.month if isinstance(d, datetime) else None,
            'day': lambda d: d.day if isinstance(d, datetime) else None,
            'hour': lambda d: d.hour if isinstance(d, datetime) else None,
            
            # Logical functions
            'if': lambda cond, true_val, false_val: true_val if cond else false_val,
            'case': self._case_function,
            
            # Type conversion
            'int': int,
            'float': float,
            'str': str,
            'bool': bool,
            
            # Null handling
            'null': lambda: None,
            'is_null': lambda v: v is None,
            'coalesce': lambda *args: next((a for a in args if a is not None), None),
        }
    
    def _case_function(self, *args) -> Any:
        """CASE WHEN expression: case(cond1, val1, cond2, val2, ..., default)"""
        if len(args) < 2:
            return None
        
        # Process pairs of condition-value
        for i in range(0, len(args) - 2, 2):
            if args[i]:
                return args[i + 1]
        
        # Default value (last arg if odd number of args)
        return args[-1] if len(args) % 2 == 1 else None
    
    def calculate_field(
        self,
        gdf: GeoDataFrame,
        expression: str,
        output_field: str,
        dtype: Optional[type] = None
    ) -> GeoDataFrame:
        """
        Calculate values for a field using expression.
        
        Args:
            gdf: GeoDataFrame
            expression: Expression string
            output_field: Output field name
            dtype: Output data type
            
        Returns:
            GeoDataFrame with new calculated field
        """
        try:
            result = gdf.copy()
            values = []
            
            for idx in range(len(gdf)):
                context = FieldExpressionContext(gdf, idx)
                value = self.evaluate_expression(expression, context)
                
                if dtype:
                    value = dtype(value) if value is not None else None
                
                values.append(value)
            
            result[output_field] = values
            return result
            
        except Exception as e:
            logger.error(f"Field calculation error: {e}")
            raise
    
    def evaluate_expression(
        self,
        expression: str,
        context: FieldExpressionContext
    ) -> Any:
        """
        Evaluate expression in given context.
        
        Args:
            expression: Expression string
            context: Evaluation context
            
        Returns:
            Expression result
        """
        try:
            # Replace field references with values
            expr = self._replace_field_refs(expression, context)
            
            # Evaluate using safer eval with limited namespace
            namespace = {
                **self.functions,
                'pi': np.pi,
                'e': np.e,
            }
            
            result = eval(expr, {"__builtins__": {}}, namespace)
            return result
            
        except Exception as e:
            logger.error(f"Expression evaluation error: {e}")
            raise
    
    def _replace_field_refs(self, expression: str, context: FieldExpressionContext) -> str:
        """Replace field references in expression with values."""
        # Find all field references like $fieldname or @fieldname
        field_pattern = r'[$@]([a-zA-Z_][a-zA-Z0-9_]*)'
        
        def replace_field(match):
            field_name = match.group(1)
            value = context.get_field_value(field_name)
            
            # Quote strings
            if isinstance(value, str):
                return f"'{value}'"
            elif value is None:
                return 'None'
            else:
                return str(value)
        
        return re.sub(field_pattern, replace_field, expression)
    
    def batch_calculate(
        self,
        gdf: GeoDataFrame,
        calculations: Dict[str, str],
        dtypes: Optional[Dict[str, type]] = None
    ) -> GeoDataFrame:
        """
        Perform multiple field calculations.
        
        Args:
            gdf: GeoDataFrame
            calculations: Dict of {output_field: expression}
            dtypes: Optional dict of output data types
            
        Returns:
            GeoDataFrame with all new fields
        """
        result = gdf.copy()
        
        for field_name, expression in calculations.items():
            dtype = dtypes.get(field_name) if dtypes else None
            result = self.calculate_field(result, expression, field_name, dtype)
        
        return result


class QueryBuilder:
    """
    Advanced query builder for attribute filtering.
    Supports complex conditions on GeoDataFrames.
    """
    
    def __init__(self, gdf: GeoDataFrame):
        self.gdf = gdf
        self.conditions = []
        self.combinator = 'AND'  # AND or OR
    
    def where(self, column: str, operator_str: str, value: Any) -> 'QueryBuilder':
        """
        Add WHERE condition.
        
        Args:
            column: Column name
            operator_str: Operator ('==', '!=', '<', '>', '<=', '>=', 'in', 'like')
            value: Comparison value
            
        Returns:
            Self for chaining
        """
        self.conditions.append({
            'column': column,
            'operator': operator_str,
            'value': value
        })
        return self
    
    def and_(self, column: str, operator_str: str, value: Any) -> 'QueryBuilder':
        """Add AND condition."""
        self.combinator = 'AND'
        return self.where(column, operator_str, value)
    
    def or_(self, column: str, operator_str: str, value: Any) -> 'QueryBuilder':
        """Add OR condition."""
        self.combinator = 'OR'
        return self.where(column, operator_str, value)
    
    def execute(self) -> GeoDataFrame:
        """
        Execute query and return filtered GeoDataFrame.
        
        Returns:
            Filtered GeoDataFrame
        """
        if not self.conditions:
            return self.gdf
        
        masks = []
        
        for cond in self.conditions:
            col = cond['column']
            op = cond['operator']
            val = cond['value']
            
            if op == '==':
                mask = self.gdf[col] == val
            elif op == '!=':
                mask = self.gdf[col] != val
            elif op == '<':
                mask = self.gdf[col] < val
            elif op == '>':
                mask = self.gdf[col] > val
            elif op == '<=':
                mask = self.gdf[col] <= val
            elif op == '>=':
                mask = self.gdf[col] >= val
            elif op == 'in':
                mask = self.gdf[col].isin(val if isinstance(val, list) else [val])
            elif op == 'like':
                mask = self.gdf[col].str.contains(val, case=False, na=False)
            elif op == 'between':
                mask = (self.gdf[col] >= val[0]) & (self.gdf[col] <= val[1])
            else:
                raise ValueError(f"Unknown operator: {op}")
            
            masks.append(mask)
        
        # Combine masks
        if self.combinator == 'AND':
            final_mask = masks[0]
            for mask in masks[1:]:
                final_mask = final_mask & mask
        else:  # OR
            final_mask = masks[0]
            for mask in masks[1:]:
                final_mask = final_mask | mask
        
        return self.gdf[final_mask].reset_index(drop=True)


# Module exports
__all__ = ['FieldCalculator', 'QueryBuilder', 'FieldExpressionContext']
