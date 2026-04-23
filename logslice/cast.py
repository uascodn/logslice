"""Field type casting: convert field values to int, float, bool, or str."""

from typing import Any, Dict, List, Tuple

_BOOL_TRUE = {"true", "1", "yes", "on"}
_BOOL_FALSE = {"false", "0", "no", "off"}


def cast_value(value: Any, target_type: str) -> Any:
    """Cast *value* to *target_type* ('int', 'float', 'bool', 'str').

    Raises ValueError if the conversion is not possible.
    """
    if target_type == "int":
        return int(value)
    if target_type == "float":
        return float(value)
    if target_type == "bool":
        if isinstance(value, bool):
            return value
        s = str(value).strip().lower()
        if s in _BOOL_TRUE:
            return True
        if s in _BOOL_FALSE:
            return False
        raise ValueError(f"Cannot cast {value!r} to bool")
    if target_type == "str":
        return str(value)
    raise ValueError(f"Unknown target type: {target_type!r}")


def cast_field(
    record: Dict[str, Any],
    field: str,
    target_type: str,
    default: Any = None,
) -> Dict[str, Any]:
    """Return a copy of *record* with *field* cast to *target_type*.

    If the field is absent or conversion fails, *default* is used (None by
    default, meaning the field is left unchanged on failure).
    """
    record = dict(record)
    if field not in record:
        return record
    try:
        record[field] = cast_value(record[field], target_type)
    except (ValueError, TypeError):
        if default is not None:
            record[field] = default
    return record


def cast_fields(
    record: Dict[str, Any],
    casts: List[Tuple[str, str]],
) -> Dict[str, Any]:
    """Apply multiple casts described by a list of (field, type) pairs."""
    for field, target_type in casts:
        record = cast_field(record, field, target_type)
    return record


def parse_cast_expr(expr: str) -> Tuple[str, str]:
    """Parse 'field:type' into (field, type).

    Examples::

        parse_cast_expr('latency:float')  -> ('latency', 'float')
        parse_cast_expr('retries:int')    -> ('retries', 'int')
    """
    if ":" not in expr:
        raise ValueError(f"Cast expression must be 'field:type', got: {expr!r}")
    field, _, target_type = expr.partition(":")
    field = field.strip()
    target_type = target_type.strip()
    if not field:
        raise ValueError("Field name must not be empty")
    allowed = {"int", "float", "bool", "str"}
    if target_type not in allowed:
        raise ValueError(f"Unknown type {target_type!r}; allowed: {allowed}")
    return field, target_type


def apply_casts(
    record: Dict[str, Any],
    exprs: List[str],
) -> Dict[str, Any]:
    """Parse and apply a list of cast expressions to *record*."""
    casts = [parse_cast_expr(e) for e in exprs]
    return cast_fields(record, casts)
