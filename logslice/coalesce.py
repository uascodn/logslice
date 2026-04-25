"""Field coalescing: return the first non-null/non-empty value from a list of fields."""

from typing import Any, Dict, List, Optional, Tuple


def _is_present(value: Any) -> bool:
    """Return True if value is considered non-null and non-empty."""
    if value is None:
        return False
    if isinstance(value, str) and value.strip() == "":
        return False
    return True


def coalesce_fields(
    record: Dict[str, Any],
    source_fields: List[str],
    target_field: str,
    default: Any = None,
) -> Dict[str, Any]:
    """Set target_field to the first present value among source_fields."""
    result = dict(record)
    for field in source_fields:
        value = record.get(field)
        if _is_present(value):
            result[target_field] = value
            return result
    result[target_field] = default
    return result


def parse_coalesce_expr(expr: str) -> Tuple[List[str], str, Any]:
    """Parse an expression like 'field1,field2->target' or 'field1,field2->target:default'.

    Returns (source_fields, target_field, default).
    """
    if "->" not in expr:
        raise ValueError(f"coalesce expression must contain '->': {expr!r}")

    sources_part, rest = expr.split("->", 1)
    source_fields = [f.strip() for f in sources_part.split(",") if f.strip()]
    if not source_fields:
        raise ValueError(f"no source fields in coalesce expression: {expr!r}")

    default: Any = None
    if ":" in rest:
        target_field, default_str = rest.split(":", 1)
        target_field = target_field.strip()
        default = default_str.strip()
    else:
        target_field = rest.strip()

    if not target_field:
        raise ValueError(f"target field is empty in coalesce expression: {expr!r}")

    return source_fields, target_field, default


def apply_coalesces(
    record: Dict[str, Any], exprs: List[str]
) -> Dict[str, Any]:
    """Apply multiple coalesce expressions to a record in order."""
    for expr in exprs:
        source_fields, target_field, default = parse_coalesce_expr(expr)
        record = coalesce_fields(record, source_fields, target_field, default)
    return record
