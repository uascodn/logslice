"""Field enrichment for log records.

Provides functions to derive or inject new fields into records based on
existing values — e.g. extracting a date from a timestamp, mapping a
status code to a label, or tagging records with a static value.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional

Record = Dict[str, Any]
Enricher = Callable[[Record], Record]


def enrich_static(record: Record, field: str, value: str) -> Record:
    """Add a static field to a record if not already present."""
    if field not in record:
        record = {**record, field: value}
    return record


def enrich_derived(record: Record, src_field: str, dst_field: str,
                   transform: Callable[[Any], Any]) -> Record:
    """Derive a new field by applying *transform* to an existing field's value.

    If *src_field* is absent the record is returned unchanged.
    """
    if src_field not in record:
        return record
    try:
        derived = transform(record[src_field])
    except Exception:
        return record
    return {**record, dst_field: derived}


def enrich_date_from_timestamp(record: Record,
                               ts_field: str = "timestamp",
                               dst_field: str = "date") -> Record:
    """Extract the date portion (YYYY-MM-DD) from an ISO-8601 timestamp field."""
    def _extract_date(value: Any) -> str:
        return str(value)[:10]

    return enrich_derived(record, ts_field, dst_field, _extract_date)


def enrich_level_label(record: Record,
                       level_field: str = "level",
                       dst_field: str = "level_label") -> Record:
    """Map a numeric or abbreviated level to a human-readable label."""
    _LABELS: Dict[str, str] = {
        "10": "trace", "20": "debug", "30": "info",
        "40": "warn",  "50": "error", "60": "fatal",
        "trace": "trace", "debug": "debug", "info": "info",
        "warn": "warn", "warning": "warn", "error": "error",
        "fatal": "fatal", "critical": "fatal",
    }

    def _map(value: Any) -> str:
        return _LABELS.get(str(value).lower(), str(value).lower())

    return enrich_derived(record, level_field, dst_field, _map)


# ---------------------------------------------------------------------------
# Expression parsing
# ---------------------------------------------------------------------------

_STATIC_RE = re.compile(r'^([\w.]+)=(.+)$')
_DERIVED_RE = re.compile(r'^([\w.]+)->([\w.]+)$')


def parse_enrich_expr(expr: str) -> Enricher:
    """Parse an enrichment expression into a callable enricher.

    Supported forms:
      ``field=value``          — inject a static field
      ``src->dst``             — copy src to dst (identity transform)
      ``date_from:<ts>``       — extract date from timestamp field *ts*
      ``level_label:<field>``  — map level field to a label
    """
    expr = expr.strip()

    if expr.startswith("date_from:"):
        ts_field = expr[len("date_from:"):].strip()
        return lambda r, f=ts_field: enrich_date_from_timestamp(r, ts_field=f)

    if expr.startswith("level_label:"):
        lf = expr[len("level_label:"):].strip()
        return lambda r, f=lf: enrich_level_label(r, level_field=f)

    m = _STATIC_RE.match(expr)
    if m:
        field, value = m.group(1), m.group(2)
        return lambda r, f=field, v=value: enrich_static(r, f, v)

    m = _DERIVED_RE.match(expr)
    if m:
        src, dst = m.group(1), m.group(2)
        return lambda r, s=src, d=dst: enrich_derived(r, s, d, lambda x: x)

    raise ValueError(f"Unrecognised enrich expression: {expr!r}")


def apply_enrichers(record: Record, enrichers: List[Enricher]) -> Record:
    """Apply a sequence of enrichers to a record in order."""
    for enricher in enrichers:
        record = enricher(record)
    return record
