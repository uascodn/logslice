"""Field transformation utilities for log records."""

from typing import Any, Callable, Dict, List, Optional


TransformFn = Callable[[Dict[str, Any]], Dict[str, Any]]


def rename_field(record: Dict[str, Any], src: str, dst: str) -> Dict[str, Any]:
    """Return a new record with field src renamed to dst."""
    if src not in record:
        return record
    result = dict(record)
    result[dst] = result.pop(src)
    return result


def drop_fields(record: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
    """Return a new record with the given fields removed."""
    return {k: v for k, v in record.items() if k not in fields}


def keep_fields(record: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
    """Return a new record containing only the specified fields."""
    return {k: record[k] for k in fields if k in record}


def add_field(record: Dict[str, Any], key: str, value: Any) -> Dict[str, Any]:
    """Return a new record with key set to value (overwrites if present)."""
    result = dict(record)
    result[key] = value
    return result


def parse_transform_expr(expr: str):
    """Parse a transform expression string into a (op, args) tuple.

    Supported forms:
      rename:old=new
      drop:field1,field2
      keep:field1,field2
      add:key=value
    """
    if ":" not in expr:
        raise ValueError(f"Invalid transform expression: {expr!r}")
    op, _, rest = expr.partition(":")
    op = op.strip().lower()
    if op == "rename":
        if "=" not in rest:
            raise ValueError(f"rename requires 'old=new', got: {rest!r}")
        src, _, dst = rest.partition("=")
        return ("rename", src.strip(), dst.strip())
    elif op == "drop":
        fields = [f.strip() for f in rest.split(",") if f.strip()]
        return ("drop", fields)
    elif op == "keep":
        fields = [f.strip() for f in rest.split(",") if f.strip()]
        return ("keep", fields)
    elif op == "add":
        if "=" not in rest:
            raise ValueError(f"add requires 'key=value', got: {rest!r}")
        key, _, value = rest.partition("=")
        return ("add", key.strip(), value.strip())
    else:
        raise ValueError(f"Unknown transform op: {op!r}")


def build_transform(expr: str) -> TransformFn:
    """Build a transform function from an expression string."""
    parsed = parse_transform_expr(expr)
    op = parsed[0]
    if op == "rename":
        _, src, dst = parsed
        return lambda r: rename_field(r, src, dst)
    elif op == "drop":
        _, fields = parsed
        return lambda r: drop_fields(r, fields)
    elif op == "keep":
        _, fields = parsed
        return lambda r: keep_fields(r, fields)
    elif op == "add":
        _, key, value = parsed
        return lambda r: add_field(r, key, value)
    raise ValueError(f"Unhandled op: {op}")


def apply_transforms(record: Dict[str, Any], transforms: List[TransformFn]) -> Dict[str, Any]:
    """Apply a list of transform functions to a record in order."""
    for fn in transforms:
        record = fn(record)
    return record
