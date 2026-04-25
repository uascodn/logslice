"""Field computation: evaluate simple arithmetic expressions over record fields."""

import re
from typing import Any, Dict, List, Optional, Tuple


def _to_number(value: Any) -> Optional[float]:
    """Coerce a value to float, returning None on failure."""
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def compute_expr(record: Dict[str, Any], expr: str) -> Optional[float]:
    """Evaluate a simple arithmetic expression using field values from record.

    Supports +, -, *, / between field references and numeric literals.
    Field references are bare identifiers; numeric literals are integers or floats.

    Example: "latency_ms / 1000", "bytes_in + bytes_out"
    """
    token_re = re.compile(r'([A-Za-z_][A-Za-z0-9_.]*|[0-9]*\.?[0-9]+|[+\-*/])')
    tokens = token_re.findall(expr.strip())
    if not tokens:
        return None

    def resolve(tok: str) -> Optional[float]:
        try:
            return float(tok)
        except ValueError:
            return _to_number(record.get(tok))

    # Simple left-to-right evaluation (no precedence, use parens not supported)
    result = resolve(tokens[0])
    if result is None:
        return None
    i = 1
    while i < len(tokens) - 1:
        op = tokens[i]
        rhs = resolve(tokens[i + 1])
        if rhs is None or op not in ('+', '-', '*', '/'):
            return None
        if op == '+': result += rhs
        elif op == '-': result -= rhs
        elif op == '*': result *= rhs
        elif op == '/':
            if rhs == 0:
                return None
            result /= rhs
        i += 2
    return result


def parse_compute_expr(expr: str) -> Tuple[str, str]:
    """Parse 'new_field=arithmetic_expr' into (field_name, expression).

    Raises ValueError on bad format.
    """
    if '=' not in expr:
        raise ValueError(f"compute expr must be 'field=expr', got: {expr!r}")
    field, _, body = expr.partition('=')
    field = field.strip()
    body = body.strip()
    if not field:
        raise ValueError("compute expr field name must not be empty")
    if not body:
        raise ValueError("compute expr body must not be empty")
    return field, body


def apply_computes(
    record: Dict[str, Any], exprs: List[Tuple[str, str]]
) -> Dict[str, Any]:
    """Apply a list of (field, expr) compute steps to a record, returning a new dict."""
    out = dict(record)
    for field, expr in exprs:
        value = compute_expr(out, expr)
        if value is not None:
            # Store as int if whole number, else float
            out[field] = int(value) if value == int(value) else value
    return out
