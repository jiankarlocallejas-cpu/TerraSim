"""
Raster Algebra and Map Algebra Expression Engine.
Supports GDAL map algebra syntax for raster operations.

Features:
- Expression parsing and evaluation
- Raster calculator with multiple bands
- Conditional expressions
- Statistical operations
- Logical operations
- Trigonometric and mathematical functions
"""

import logging
import re
from typing import Dict, Any, List, Optional, Callable, Union
import numpy as np
from dataclasses import dataclass
import rasterio
from rasterio.io import MemoryFile
try:
    import numexpr as ne  # type: ignore
except ImportError:
    ne = None  # type: ignore
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class RasterAlgebraContext:
    """Context for raster algebra operations."""
    rasters: Dict[str, np.ndarray]  # Named raster arrays
    band_indices: Dict[str, int]    # Band index for each raster
    nodata_value: float = -9999
    dtype: Any = np.float32


class AlgebraToken:
    """Token in algebra expression."""
    
    TOKEN_TYPES = {
        'NUMBER': r'-?\d+\.?\d*([eE][+-]?\d+)?',
        'RASTER': r'[a-zA-Z_][a-zA-Z0-9_]*',
        'FUNCTION': r'(sin|cos|tan|sqrt|exp|log|abs|min|max|mean|std|sum|where)',
        'OPERATOR': r'[\+\-\*\/\^]',
        'COMPARISON': r'(==|!=|<=|>=|<|>)',
        'LOGICAL': r'(and|or|not)',
        'LPAREN': r'\(',
        'RPAREN': r'\)',
        'COMMA': r',',
        'WHITESPACE': r'\s+',
    }
    
    def __init__(self, type_: str, value: str):
        self.type = type_
        self.value = value
    
    def __repr__(self):
        return f"Token({self.type}, {self.value})"


class ExpressionLexer:
    """Tokenize map algebra expressions."""
    
    def __init__(self, expression: str):
        self.expression = expression.strip()
        self.pos = 0
        self.tokens: List[AlgebraToken] = []
    
    def tokenize(self) -> List[AlgebraToken]:
        """Tokenize expression into tokens."""
        while self.pos < len(self.expression):
            matched = False
            
            for token_type, pattern in AlgebraToken.TOKEN_TYPES.items():
                regex = re.compile(f'^({pattern})', re.IGNORECASE)
                match = regex.match(self.expression, self.pos)
                
                if match:
                    value = match.group(0)
                    
                    if token_type != 'WHITESPACE':
                        self.tokens.append(AlgebraToken(token_type, value))
                    
                    self.pos = match.end()
                    matched = True
                    break
            
            if not matched:
                raise SyntaxError(f"Invalid token at position {self.pos}: {self.expression[self.pos]}")
        
        return self.tokens


class ExpressionParser:
    """Parse map algebra expressions into AST."""
    
    def __init__(self, tokens: List[AlgebraToken]):
        self.tokens = tokens
        self.pos = 0
    
    def parse(self) -> 'ASTNode':
        """Parse tokens into expression tree."""
        return self._parse_expression()
    
    def _current_token(self) -> Optional[AlgebraToken]:
        """Get current token without advancing."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None
    
    def _consume(self, expected_type: Optional[str] = None) -> AlgebraToken:
        """Consume and return current token."""
        token = self._current_token()
        if token is None:
            raise SyntaxError("Unexpected end of expression")
        if expected_type and token.type != expected_type:
            raise SyntaxError(f"Expected {expected_type}, got {token.type}")
        self.pos += 1
        return token
    
    def _parse_expression(self) -> 'ASTNode':
        """Parse logical OR expression."""
        left = self._parse_and_expr()
        
        token = self._current_token()
        while token and token.type == 'LOGICAL' and token.value.lower() == 'or':  # type: ignore
            self._consume()
            right = self._parse_and_expr()
            left = BinaryOpNode('or', left, right)
            token = self._current_token()
        
        return left
    
    def _parse_and_expr(self) -> 'ASTNode':
        """Parse logical AND expression."""
        left = self._parse_comparison()
        
        token = self._current_token()
        while token and token.type == 'LOGICAL' and token.value.lower() == 'and':  # type: ignore
            self._consume()
            right = self._parse_comparison()
            left = BinaryOpNode('and', left, right)
            token = self._current_token()
        
        return left
    
    def _parse_comparison(self) -> 'ASTNode':
        """Parse comparison expression."""
        left = self._parse_additive()
        
        token = self._current_token()
        while token and token.type == 'COMPARISON':
            op_token = self._consume()
            right = self._parse_additive()
            left = BinaryOpNode(op_token.value, left, right)  # type: ignore
            token = self._current_token()
        
        return left
    
    def _parse_additive(self) -> 'ASTNode':
        """Parse addition and subtraction."""
        left = self._parse_multiplicative()
        
        token = self._current_token()
        while token and token.type == 'OPERATOR' and token.value in ['+', '-']:  # type: ignore
            op_token = self._consume()
            right = self._parse_multiplicative()
            left = BinaryOpNode(op_token.value, left, right)  # type: ignore
            token = self._current_token()
        
        return left
    
    def _parse_multiplicative(self) -> 'ASTNode':
        """Parse multiplication and division."""
        left = self._parse_power()
        
        token = self._current_token()
        while token and token.type == 'OPERATOR' and token.value in ['*', '/']:  # type: ignore
            op_token = self._consume()
            right = self._parse_power()
            left = BinaryOpNode(op_token.value, left, right)  # type: ignore
            token = self._current_token()
        
        return left
    
    def _parse_power(self) -> 'ASTNode':
        """Parse exponentiation."""
        left = self._parse_unary()
        
        token = self._current_token()
        if token and token.type == 'OPERATOR' and token.value == '^':  # type: ignore
            self._consume()
            right = self._parse_power()  # Right associative
            left = BinaryOpNode('^', left, right)
        
        return left
    
    def _parse_unary(self) -> 'ASTNode':
        """Parse unary expressions."""
        token = self._current_token()
        if token and token.type == 'LOGICAL' and token.value.lower() == 'not':  # type: ignore
            self._consume()
            expr = self._parse_unary()
            return UnaryOpNode('not', expr)
        
        if token and token.type == 'OPERATOR' and token.value in ['+', '-']:  # type: ignore
            op_token = self._consume()
            expr = self._parse_unary()
            return UnaryOpNode(op_token.value, expr)  # type: ignore
        
        return self._parse_primary()
    
    def _parse_primary(self) -> 'ASTNode':
        """Parse primary expressions."""
        token = self._current_token()
        
        # Function call
        if token and token.type == 'FUNCTION':
            func_token = self._consume()
            self._consume('LPAREN')
            args = []
            
            next_token = self._current_token()
            if not (next_token and next_token.type == 'RPAREN'):
                args.append(self._parse_expression())
                
                next_token = self._current_token()
                while next_token and next_token.type == 'COMMA':
                    self._consume()
                    args.append(self._parse_expression())
                    next_token = self._current_token()
            
            self._consume('RPAREN')
            return FunctionNode(func_token.value.lower(), args)
        
        # Parenthesized expression
        if token and token.type == 'LPAREN':
            self._consume()
            expr = self._parse_expression()
            self._consume('RPAREN')
            return expr
        
        # Number
        if token and token.type == 'NUMBER':
            num_token = self._consume()
            return NumberNode(float(num_token.value))
        
        # Raster or variable
        if token and token.type == 'RASTER':
            ident_token = self._consume()
            return RasterNode(ident_token.value)
        
        raise SyntaxError(f"Unexpected token: {token}")


class ASTNode(ABC):
    """Abstract syntax tree node."""
    
    @abstractmethod
    def evaluate(self, context: RasterAlgebraContext) -> np.ndarray:
        """Evaluate node in given context."""
        pass


class NumberNode(ASTNode):
    """Literal number node."""
    
    def __init__(self, value: float):
        self.value = value
    
    def evaluate(self, context: RasterAlgebraContext) -> np.ndarray:
        return np.full_like(next(iter(context.rasters.values())), self.value, dtype=context.dtype)


class RasterNode(ASTNode):
    """Raster/variable reference node."""
    
    def __init__(self, name: str):
        self.name = name
    
    def evaluate(self, context: RasterAlgebraContext) -> np.ndarray:
        if self.name not in context.rasters:
            raise ValueError(f"Unknown raster: {self.name}")
        return context.rasters[self.name].astype(context.dtype)


class BinaryOpNode(ASTNode):
    """Binary operation node."""
    
    def __init__(self, op: str, left: ASTNode, right: ASTNode):
        self.op = op
        self.left = left
        self.right = right
    
    def evaluate(self, context: RasterAlgebraContext) -> np.ndarray:
        left_val = self.left.evaluate(context)
        right_val = self.right.evaluate(context)
        
        if ne is None:
            # Fallback without numexpr
            if self.op == '+':
                return left_val + right_val  # type: ignore
            elif self.op == '-':
                return left_val - right_val  # type: ignore
            elif self.op == '*':
                return left_val * right_val  # type: ignore
            elif self.op == '/':
                return left_val / right_val  # type: ignore
            elif self.op == '^':
                return left_val ** right_val  # type: ignore
            elif self.op == '==':
                return left_val == right_val  # type: ignore
            elif self.op == '!=':
                return left_val != right_val  # type: ignore
            elif self.op == '<':
                return left_val < right_val  # type: ignore
            elif self.op == '>':
                return left_val > right_val  # type: ignore
            elif self.op == '<=':
                return left_val <= right_val  # type: ignore
            elif self.op == '>=':
                return left_val >= right_val  # type: ignore
            elif self.op == 'and':
                return left_val & right_val  # type: ignore
            elif self.op == 'or':
                return left_val | right_val  # type: ignore
            else:
                raise ValueError(f"Unknown operator: {self.op}")
        
        # Use numexpr
        if self.op == '+':
            return ne.evaluate('left_val + right_val')  # type: ignore
        elif self.op == '-':
            return ne.evaluate('left_val - right_val')  # type: ignore
        elif self.op == '*':
            return ne.evaluate('left_val * right_val')  # type: ignore
        elif self.op == '/':
            return ne.evaluate('left_val / right_val')  # type: ignore
        elif self.op == '^':
            return ne.evaluate('left_val ** right_val')  # type: ignore
        elif self.op == '==':
            return ne.evaluate('left_val == right_val')  # type: ignore
        elif self.op == '!=':
            return ne.evaluate('left_val != right_val')  # type: ignore
        elif self.op == '<':
            return ne.evaluate('left_val < right_val')  # type: ignore
        elif self.op == '>':
            return ne.evaluate('left_val > right_val')  # type: ignore
        elif self.op == '<=':
            return ne.evaluate('left_val <= right_val')  # type: ignore
        elif self.op == '>=':
            return ne.evaluate('left_val >= right_val')  # type: ignore
        elif self.op == 'and':
            return ne.evaluate('left_val & right_val')  # type: ignore
        elif self.op == 'or':
            return ne.evaluate('left_val | right_val')  # type: ignore
        else:
            raise ValueError(f"Unknown operator: {self.op}")


class UnaryOpNode(ASTNode):
    """Unary operation node."""
    
    def __init__(self, op: str, operand: ASTNode):
        self.op = op
        self.operand = operand
    
    def evaluate(self, context: RasterAlgebraContext) -> np.ndarray:
        val = self.operand.evaluate(context)
        
        if ne is None:
            # Fallback without numexpr
            if self.op == '-':
                return -val  # type: ignore
            elif self.op == '+':
                return val
            elif self.op == 'not':
                return ~val  # type: ignore
            else:
                raise ValueError(f"Unknown unary operator: {self.op}")
        
        if self.op == '-':
            return ne.evaluate('-val')  # type: ignore
        elif self.op == '+':
            return val
        elif self.op == 'not':
            return ne.evaluate('~val')  # type: ignore
        else:
            raise ValueError(f"Unknown unary operator: {self.op}")


class FunctionNode(ASTNode):
    """Function call node."""
    
    def __init__(self, name: str, args: List[ASTNode]):
        self.name = name
        self.args = args
    
    def evaluate(self, context: RasterAlgebraContext) -> np.ndarray:
        arg_vals = [arg.evaluate(context) for arg in self.args]
        
        # Use numpy for common functions that work regardless of numexpr
        if self.name == 'min':
            return np.minimum(*arg_vals)  # type: ignore
        elif self.name == 'max':
            return np.maximum(*arg_vals)  # type: ignore
        elif self.name == 'mean':
            return np.mean(arg_vals, axis=0)  # type: ignore
        elif self.name == 'std':
            return np.std(arg_vals, axis=0)  # type: ignore
        elif self.name == 'sum':
            return np.sum(arg_vals, axis=0)  # type: ignore
        elif self.name == 'where':
            if len(arg_vals) != 3:
                raise ValueError("where() requires 3 arguments")
            return np.where(arg_vals[0], arg_vals[1], arg_vals[2])  # type: ignore
        
        # For math functions, check if numexpr is available
        if ne is None:
            # Fallback using numpy
            if self.name == 'sin':
                return np.sin(arg_vals[0])  # type: ignore
            elif self.name == 'cos':
                return np.cos(arg_vals[0])  # type: ignore
            elif self.name == 'tan':
                return np.tan(arg_vals[0])  # type: ignore
            elif self.name == 'sqrt':
                return np.sqrt(arg_vals[0])  # type: ignore
            elif self.name == 'exp':
                return np.exp(arg_vals[0])  # type: ignore
            elif self.name == 'log':
                return np.log(arg_vals[0])  # type: ignore
            elif self.name == 'abs':
                return np.abs(arg_vals[0])  # type: ignore
            else:
                raise ValueError(f"Unknown function: {self.name}")
        
        # Use numexpr for fast evaluation
        if self.name == 'sin':
            return ne.evaluate('sin(arg_vals[0])')  # type: ignore
        elif self.name == 'cos':
            return ne.evaluate('cos(arg_vals[0])')  # type: ignore
        elif self.name == 'tan':
            return ne.evaluate('tan(arg_vals[0])')  # type: ignore
        elif self.name == 'sqrt':
            return ne.evaluate('sqrt(arg_vals[0])')  # type: ignore
        elif self.name == 'exp':
            return ne.evaluate('exp(arg_vals[0])')  # type: ignore
        elif self.name == 'log':
            return ne.evaluate('log(arg_vals[0])')  # type: ignore
        elif self.name == 'abs':
            return ne.evaluate('abs(arg_vals[0])')  # type: ignore
        else:
            raise ValueError(f"Unknown function: {self.name}")


class RasterAlgebra:
    """
    Raster algebra expression evaluator.
    Parses and evaluates map algebra expressions.
    """
    
    def evaluate(
        self,
        expression: str,
        rasters: Dict[str, np.ndarray],
        nodata_value: float = -9999,
        dtype: Any = np.float32
    ) -> np.ndarray:
        """
        Evaluate raster algebra expression.
        
        Args:
            expression: Map algebra expression (e.g., "(B1 + B2) / 2")
            rasters: Dict of named raster arrays
            nodata_value: NoData value
            dtype: Output data type
            
        Returns:
            Result array
        """
        try:
            # Tokenize
            lexer = ExpressionLexer(expression)
            tokens = lexer.tokenize()
            
            # Parse
            parser = ExpressionParser(tokens)
            ast = parser.parse()
            
            # Evaluate
            context = RasterAlgebraContext(
                rasters=rasters,
                band_indices={},
                nodata_value=nodata_value,
                dtype=dtype
            )
            
            result = ast.evaluate(context)
            
            # Handle NoData
            for raster in rasters.values():
                result = np.where(raster == nodata_value, nodata_value, result)
            
            return result.astype(dtype)
            
        except Exception as e:
            logger.error(f"Raster algebra evaluation error: {e}")
            raise


# Module exports
__all__ = ['RasterAlgebra', 'RasterAlgebraContext', 'ExpressionLexer', 'ExpressionParser']
