"""Compare two log streams and report differing records."""
from __future__ import annotations

from typing import Iterable, Iterator

from logslice.parser import parse_line


def _key(record: dict, key_fields: list[str]) -> tuple:
    return tuple(record.get(f) for f in key_fields)


def index_records(
    lines: Iterable[str], key_fields: list[str]
) -> dict[tuple, dict]:
    """Parse lines and index by key_fields."""
    index: dict[tuple, dict] = {}
    for line in lines:
        rec = parse_line(line.rstrip("\n"))
        if rec is None:
            continue
        k = _key(rec, key_fields)
        index[k] = rec
    return index


def compare_streams(
    lines_a: Iterable[str],
    lines_b: Iterable[str],
    key_fields: list[str],
    compare_fields: list[str] | None = None,
) -> Iterator[dict]:
    """Yield diff records describing mismatches between two log streams."""
    index_a = index_records(lines_a, key_fields)
    index_b = index_records(lines_b, key_fields)

    all_keys = set(index_a) | set(index_b)
    for key in sorted(all_keys, key=lambda k: [str(x) for x in k]):
        in_a = key in index_a
        in_b = key in index_b
        if in_a and not in_b:
            yield {"status": "only_in_a", "key": dict(zip(key_fields, key))}
        elif in_b and not in_a:
            yield {"status": "only_in_b", "key": dict(zip(key_fields, key))}
        else:
            rec_a, rec_b = index_a[key], index_b[key]
            fields = compare_fields or (set(rec_a) | set(rec_b))
            diffs: dict[str, dict] = {}
            for f in fields:
                va, vb = rec_a.get(f), rec_b.get(f)
                if va != vb:
                    diffs[f] = {"a": va, "b": vb}
            if diffs:
                yield {
                    "status": "changed",
                    "key": dict(zip(key_fields, key)),
                    "diffs": diffs,
                }
