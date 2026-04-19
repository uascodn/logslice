"""Output writer for logslice — handles writing formatted records to a stream or file."""

import sys
from typing import Any, Dict, Iterable, IO, Optional

from logslice.output import format_record, SUPPORTED_FORMATS


class Writer:
    def __init__(self, fmt: str = "json", stream: Optional[IO[str]] = None):
        if fmt not in SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {fmt!r}")
        self.fmt = fmt
        self.stream = stream or sys.stdout
        self._count = 0

    def write(self, record: Dict[str, Any]) -> None:
        line = format_record(record, fmt=self.fmt)
        self.stream.write(line + "\n")
        self._count += 1

    def write_all(self, records: Iterable[Dict[str, Any]]) -> int:
        for record in records:
            self.write(record)
        return self._count

    @property
    def count(self) -> int:
        return self._count


def write_records(
    records: Iterable[Dict[str, Any]],
    fmt: str = "json",
    stream: Optional[IO[str]] = None,
) -> int:
    """Convenience function: write all records and return count written."""
    writer = Writer(fmt=fmt, stream=stream)
    return writer.write_all(records)
