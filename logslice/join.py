"""Join two streams of log records on a common field.

Supports inner join (only matched records) and left join (all records from
the left stream, with right-side fields merged in when a match is found).
"""

from __future__ import annotations

from typing import Dict, Iterable, Iterator, List, Optional


def index_right(
    records: Iterable[dict],
    key_field: str,
) -> Dict[str, List[dict]]:
    """Build an index of right-side records keyed by *key_field*.

    Multiple records with the same key are stored in a list so that a
    one-to-many join is possible.
    """
    index: Dict[str, List[dict]] = {}
    for rec in records:
        key = str(rec.get(key_field, ""))
        if key:
            index.setdefault(key, []).append(rec)
    return index


def _merge(left: dict, right: dict, prefix: str) -> dict:
    """Merge *right* into a copy of *left*.

    Right-side keys are prefixed with *prefix* (e.g. ``"right_"``) to avoid
    silently clobbering left-side fields.
    """
    merged = dict(left)
    for k, v in right.items():
        dest_key = f"{prefix}{k}" if k in left else k
        merged[dest_key] = v
    return merged


def inner_join(
    left: Iterable[dict],
    right_index: Dict[str, List[dict]],
    key_field: str,
    prefix: str = "right_",
) -> Iterator[dict]:
    """Yield merged records for every left record that has a match in *right_index*.

    When a left record matches multiple right records each combination is
    emitted as a separate output record.
    """
    for rec in left:
        key = str(rec.get(key_field, ""))
        matches = right_index.get(key)
        if matches:
            for right_rec in matches:
                yield _merge(rec, right_rec, prefix)


def left_join(
    left: Iterable[dict],
    right_index: Dict[str, List[dict]],
    key_field: str,
    prefix: str = "right_",
) -> Iterator[dict]:
    """Yield all left records, enriched with right-side fields when available.

    Unmatched left records are emitted unchanged.
    """
    for rec in left:
        key = str(rec.get(key_field, ""))
        matches = right_index.get(key)
        if matches:
            for right_rec in matches:
                yield _merge(rec, right_rec, prefix)
        else:
            yield dict(rec)


def parse_join_expr(expr: str) -> dict:
    """Parse a join expression string into a configuration dict.

    Accepted formats::

        "field=request_id"              -> inner join on request_id
        "field=request_id,type=left"    -> left join on request_id
        "field=request_id,prefix=r_"    -> inner join, custom prefix

    Returns a dict with keys: ``field``, ``type`` (``"inner"`` or ``"left"``),
    ``prefix``.

    Raises ``ValueError`` for malformed expressions.
    """
    config: dict = {"type": "inner", "prefix": "right_", "field": None}
    for part in expr.split(","):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise ValueError(f"Invalid join expression segment (missing '='): {part!r}")
        k, v = part.split("=", 1)
        k = k.strip()
        v = v.strip()
        if k == "field":
            config["field"] = v
        elif k == "type":
            if v not in ("inner", "left"):
                raise ValueError(f"Unknown join type {v!r}; expected 'inner' or 'left'")
            config["type"] = v
        elif k == "prefix":
            config["prefix"] = v
        else:
            raise ValueError(f"Unknown join option: {k!r}")
    if not config["field"]:
        raise ValueError("Join expression must specify 'field=<name>'")
    return config


def apply_join(
    left: Iterable[dict],
    right: Iterable[dict],
    expr: str,
) -> Iterator[dict]:
    """High-level helper: parse *expr*, index *right*, then join with *left*."""
    config = parse_join_expr(expr)
    right_index = index_right(right, config["field"])
    if config["type"] == "left":
        return left_join(left, right_index, config["field"], config["prefix"])
    return inner_join(left, right_index, config["field"], config["prefix"])
