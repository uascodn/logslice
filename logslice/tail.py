"""Tail support: read last N lines or follow a file for new log entries."""

from __future__ import annotations

import collections
import os
import time
from typing import Iterable, Iterator


def last_n_lines(path: str, n: int) -> list[str]:
    """Return the last *n* lines of *path* without reading the whole file."""
    if n <= 0:
        return []
    with open(path, "rb") as fh:
        # Use a deque so we naturally keep only the last n lines.
        buf: collections.deque[bytes] = collections.deque(maxlen=n)
        for raw in fh:
            buf.append(raw)
    return [line.decode("utf-8", errors="replace").rstrip("\n") for line in buf]


def follow_file(path: str, poll_interval: float = 0.25) -> Iterator[str]:
    """Yield new lines appended to *path*, blocking between polls.

    Starts from the *current* end of the file so only future writes are
    returned.  Raises ``FileNotFoundError`` if *path* does not exist when
    called.
    """
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        # Seek to end so we only tail new content.
        fh.seek(0, os.SEEK_END)
        while True:
            line = fh.readline()
            if line:
                yield line.rstrip("\n")
            else:
                time.sleep(poll_interval)


def parse_tail_expr(expr: str) -> int:
    """Parse a tail expression such as ``'50'`` and return the integer count.

    Raises ``ValueError`` for non-positive or non-numeric values.
    """
    try:
        n = int(expr)
    except ValueError:
        raise ValueError(f"tail count must be an integer, got: {expr!r}")
    if n < 1:
        raise ValueError(f"tail count must be >= 1, got: {n}")
    return n


def tail_records(path: str, n: int) -> Iterable[str]:
    """Convenience wrapper: return last *n* raw lines from *path*."""
    return last_n_lines(path, n)
