"""Conditional field labeling based on field value rules."""

from __future__ import annotations

from typing import Any


def _matches(value: Any, pattern: str) -> bool:
    """Return True if str(value) equals pattern (case-insensitive)."""
    return str(value).lower() == pattern.lower()


def label_field(
    record: dict,
    source_field: str,
    target_field: str,
    rules: list[tuple[str, str]],
    default: str | None = None,
) -> dict:
    """Add *target_field* to *record* by mapping *source_field* through *rules*.

    *rules* is a list of (pattern, label) pairs tried in order.  The first
    match wins.  If nothing matches, *default* is used (or the field is
    omitted when *default* is None).
    """
    record = dict(record)
    raw = record.get(source_field)
    if raw is None:
        if default is not None:
            record[target_field] = default
        return record
    for pattern, label in rules:
        if _matches(raw, pattern):
            record[target_field] = label
            return record
    if default is not None:
        record[target_field] = default
    return record


def apply_labels(
    records: list[dict],
    source_field: str,
    target_field: str,
    rules: list[tuple[str, str]],
    default: str | None = None,
) -> list[dict]:
    """Apply :func:`label_field` to every record in *records*."""
    return [
        label_field(r, source_field, target_field, rules, default)
        for r in records
    ]


def parse_label_expr(expr: str) -> tuple[str, str, list[tuple[str, str]], str | None]:
    """Parse a label expression string.

    Format::

        source_field->target_field:val1=label1,val2=label2[,*=default]

    Example::

        level->severity:error=critical,warn=warning,info=info,*=unknown
    """
    if "->" not in expr or ":" not in expr:
        raise ValueError(
            "label expr must be 'src->dst:val=label,...' "
            f"(got {expr!r})"
        )
    fields_part, rules_part = expr.split(":", 1)
    source_field, target_field = fields_part.split("->", 1)
    source_field = source_field.strip()
    target_field = target_field.strip()
    if not source_field or not target_field:
        raise ValueError("source and target field names must not be empty")
    rules: list[tuple[str, str]] = []
    default: str | None = None
    for token in rules_part.split(","):
        token = token.strip()
        if "=" not in token:
            raise ValueError(f"invalid rule token {token!r}, expected 'val=label'")
        k, v = token.split("=", 1)
        k = k.strip()
        v = v.strip()
        if k == "*":
            default = v
        else:
            rules.append((k, v))
    return source_field, target_field, rules, default
