"""Utilities for flattening and unflattening nested log records."""
from typing import Any, Dict, Optional


def flatten_record(
    record: Dict[str, Any],
    separator: str = ".",
    prefix: str = "",
    max_depth: Optional[int] = None,
    _depth: int = 0,
) -> Dict[str, Any]:
    """Flatten a nested dict into a single-level dict with dotted keys."""
    result: Dict[str, Any] = {}
    for key, value in record.items():
        full_key = f"{prefix}{separator}{key}" if prefix else key
        if (
            isinstance(value, dict)
            and value
            and (max_depth is None or _depth < max_depth)
        ):
            nested = flatten_record(
                value,
                separator=separator,
                prefix=full_key,
                max_depth=max_depth,
                _depth=_depth + 1,
            )
            result.update(nested)
        else:
            result[full_key] = value
    return result


def unflatten_record(
    record: Dict[str, Any], separator: str = "."
) -> Dict[str, Any]:
    """Reconstruct a nested dict from a flat dict with dotted keys."""
    result: Dict[str, Any] = {}
    for key, value in record.items():
        parts = key.split(separator)
        target = result
        for part in parts[:-1]:
            if part not in target or not isinstance(target[part], dict):
                target[part] = {}
            target = target[part]
        target[parts[-1]] = value
    return result


def parse_flatten_expr(expr: str) -> Dict[str, Any]:
    """Parse a flatten expression like 'sep=/' or 'depth=2'."""
    opts: Dict[str, Any] = {"separator": ".", "max_depth": None}
    for part in expr.split(","):
        part = part.strip()
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        k, v = k.strip(), v.strip()
        if k in ("sep", "separator"):
            opts["separator"] = v
        elif k in ("depth", "max_depth"):
            opts["max_depth"] = int(v)
    return opts
