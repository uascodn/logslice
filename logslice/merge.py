"""merge.py — merge multiple sorted log streams into a single time-ordered stream.

Supports merging two or more iterables of parsed log records by timestamp,
producing a single iterator in ascending chronological order (stable sort on
tie-breaking by stream index).
"""

from __future__ import annotations

import heapq
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

from logslice.timerange import extract_timestamp


def _ts_key(record: Dict, stream_idx: int, seq: int) -> Tuple:
    """Build a heap key for a record.

    Records without a parseable timestamp are placed *after* all timestamped
    records (None sorts higher than any datetime when we use a sentinel).
    """
    ts = extract_timestamp(record)
    if ts is None:
        # Use a far-future sentinel so un-timestamped records sink to the end.
        return (1, stream_idx, seq)
    return (0, ts, stream_idx, seq)


def merge_streams(
    *streams: Iterable[Dict],
    timestamp_field: Optional[str] = None,
) -> Iterator[Dict]:
    """Merge *streams* into a single time-ordered iterator.

    Parameters
    ----------
    *streams:
        Two or more iterables of parsed log record dicts.
    timestamp_field:
        Unused directly — ``extract_timestamp`` is called internally and
        honours the standard timestamp field names automatically.  Kept for
        API symmetry with other logslice helpers.

    Yields
    ------
    dict
        Records in ascending timestamp order.  Records sharing the same
        timestamp are emitted in stream-index order (stable merge).
    """
    # heap entries: (sort_key_tuple, record)
    heap: List[Tuple] = []
    iterators = [iter(s) for s in streams]
    seq = 0  # global sequence counter for stable ordering

    # Seed the heap with the first record from each stream.
    for idx, it in enumerate(iterators):
        try:
            record = next(it)
            key = _ts_key(record, idx, seq)
            heapq.heappush(heap, (key, idx, seq, record))
            seq += 1
        except StopIteration:
            pass

    while heap:
        key, idx, _seq, record = heapq.heappop(heap)
        yield record

        # Advance the exhausted stream.
        try:
            nxt = next(iterators[idx])
            nkey = _ts_key(nxt, idx, seq)
            heapq.heappush(heap, (nkey, idx, seq, nxt))
            seq += 1
        except StopIteration:
            pass


def parse_merge_expr(expr: str) -> List[str]:
    """Parse a comma-separated list of file paths from *expr*.

    Example
    -------
    >>> parse_merge_expr("a.log, b.log, c.log")
    ['a.log', 'b.log', 'c.log']

    Raises
    ------
    ValueError
        If fewer than two paths are provided.
    """
    paths = [p.strip() for p in expr.split(",") if p.strip()]
    if len(paths) < 2:
        raise ValueError(
            f"merge requires at least two file paths, got: {expr!r}"
        )
    return paths
