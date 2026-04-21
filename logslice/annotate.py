"""Annotate log records with computed or static labels."""
from __future__ import annotations

import re
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional

Record = Dict[str, Any]


def annotate_static(records: Iterable[Record], field: str, value: Any) -> Iterator[Record]:
    """Add a fixed value to every record under *field*."""
    for rec in records:
        out = dict(rec)
        out[field] = value
        yield out


def annotate_index(records: Iterable[Record], field: str = "_index", start: int = 0) -> Iterator[Record]:
    """Annotate each record with its sequential position."""
    for i, rec in enumerate(records, start=start):
        out = dict(rec)
        out[field] = i
        yield out


def annotate_derived(
    records: Iterable[Record],
    field: str,
    expr: str,
) -> Iterator[Record]:
    """Annotate using a Python f-string-style template evaluated against the record.

    Example expr: ``"{service}-{env}"``
    """
    pattern = re.compile(r"\{(\w+)\}")

    def _render(rec: Record) -> str:
        def _sub(m: re.Match) -> str:
            key = m.group(1)
            return str(rec.get(key, ""))
        return pattern.sub(_sub, expr)

    for rec in records:
        out = dict(rec)
        out[field] = _render(rec)
        yield out


def annotate_conditional(
    records: Iterable[Record],
    field: str,
    condition_field: str,
    condition_value: str,
    true_value: Any,
    false_value: Any = None,
) -> Iterator[Record]:
    """Set *field* based on whether *condition_field* equals *condition_value*."""
    for rec in records:
        out = dict(rec)
        if str(rec.get(condition_field, "")) == condition_value:
            out[field] = true_value
        else:
            out[field] = false_value
        yield out


def parse_annotate_expr(expr: str) -> dict:
    """Parse an annotation expression string.

    Formats:
      ``field=value``               → static annotation
      ``field={src_field}``         → derived (template)
      ``field=?cond_field:yes:no``  → conditional
    """
    if "=" not in expr:
        raise ValueError(f"Invalid annotate expression (missing '='): {expr!r}")
    field, _, rhs = expr.partition("=")
    field = field.strip()
    rhs = rhs.strip()
    if rhs.startswith("?"):
        # conditional: ?cond_field:true_val:false_val
        inner = rhs[1:]
        parts = inner.split(":")
        if len(parts) < 2:
            raise ValueError(f"Conditional annotate needs at least cond:true: {expr!r}")
        return {
            "type": "conditional",
            "field": field,
            "condition_field": parts[0],
            "condition_value": parts[1],
            "true_value": parts[2] if len(parts) > 2 else True,
            "false_value": parts[3] if len(parts) > 3 else None,
        }
    if re.search(r"\{\w+\}", rhs):
        return {"type": "derived", "field": field, "expr": rhs}
    return {"type": "static", "field": field, "value": rhs}


def apply_annotation(records: Iterable[Record], spec: dict) -> Iterator[Record]:
    """Dispatch to the correct annotator based on *spec['type']*."""
    kind = spec.get("type")
    if kind == "static":
        return annotate_static(records, spec["field"], spec["value"])
    if kind == "derived":
        return annotate_derived(records, spec["field"], spec["expr"])
    if kind == "conditional":
        return annotate_conditional(
            records,
            spec["field"],
            spec["condition_field"],
            spec["condition_value"],
            spec["true_value"],
            spec["false_value"],
        )
    raise ValueError(f"Unknown annotation type: {kind!r}")
