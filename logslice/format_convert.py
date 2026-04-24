"""Convert records between output formats (JSON, logfmt, CSV, TSV)."""
from __future__ import annotations

import csv
import io
import json
from typing import Any, Dict, Iterable, Iterator, List, Optional

Record = Dict[str, Any]

SUPPORTED_FORMATS = ("json", "logfmt", "csv", "tsv")


def _logfmt_value(v: Any) -> str:
    s = str(v)
    if " " in s or "=" in s or '"' in s:
        escaped = s.replace('"', '\\"')
        return f'"{escaped}"'
    return s


def record_to_json(record: Record) -> str:
    return json.dumps(record)


def record_to_logfmt(record: Record) -> str:
    return " ".join(f"{k}={_logfmt_value(v)}" for k, v in record.items())


def records_to_csv(
    records: Iterable[Record],
    columns: Optional[List[str]] = None,
    delimiter: str = ",",
) -> Iterator[str]:
    """Yield CSV/TSV rows (header first) from an iterable of records."""
    buf = io.StringIO()
    writer: Optional[csv.DictWriter] = None
    for record in records:
        if writer is None:
            cols = columns or list(record.keys())
            writer = csv.DictWriter(
                buf, fieldnames=cols, extrasaction="ignore",
                delimiter=delimiter, lineterminator="\n"
            )
            writer.writeheader()
            yield buf.getvalue()
            buf.seek(0)
            buf.truncate()
        writer.writerow(record)
        yield buf.getvalue()
        buf.seek(0)
        buf.truncate()


def parse_format_expr(expr: str) -> Dict[str, Any]:
    """Parse a format expression like 'csv:col1,col2' or 'tsv' or 'json'."""
    parts = expr.strip().split(":", 1)
    fmt = parts[0].lower()
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format '{fmt}'. Choose from: {SUPPORTED_FORMATS}")
    columns: Optional[List[str]] = None
    if len(parts) == 2 and parts[1]:
        columns = [c.strip() for c in parts[1].split(",") if c.strip()]
    return {"format": fmt, "columns": columns}


def convert_record(record: Record, fmt: str, columns: Optional[List[str]] = None) -> str:
    if fmt == "json":
        return record_to_json(record)
    if fmt == "logfmt":
        return record_to_logfmt(record)
    raise ValueError(f"Use records_to_csv for format '{fmt}'")
