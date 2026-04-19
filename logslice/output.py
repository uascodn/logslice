"""Output formatting for logslice records."""

import json
from typing import Any, Dict, Optional


SUPPORTED_FORMATS = ("json", "logfmt", "pretty")


def format_json(record: Dict[str, Any]) -> str:
    return json.dumps(record, default=str)


def format_logfmt(record: Dict[str, Any]) -> str:
    parts = []
    for key, value in record.items():
        str_val = str(value) if not isinstance(value, str) else value
        if " " in str_val or "=" in str_val or '"' in str_val:
            str_val = '"' + str_val.replace('"', '\\"') + '"'
        parts.append(f"{key}={str_val}")
    return " ".join(parts)


def format_pretty(record: Dict[str, Any]) -> str:
    lines = []
    # Prioritize common fields first
    priority = ["timestamp", "ts", "time", "level", "msg", "message"]
    keys = sorted(record.keys(), key=lambda k: (k not in priority, priority.index(k) if k in priority else k))
    for key in keys:
        lines.append(f"  {key}: {record[key]}")
    return "---\n" + "\n".join(lines)


def format_record(record: Dict[str, Any], fmt: str = "json") -> str:
    if fmt == "json":
        return format_json(record)
    elif fmt == "logfmt":
        return format_logfmt(record)
    elif fmt == "pretty":
        return format_pretty(record)
    else:
        raise ValueError(f"Unsupported format: {fmt!r}. Choose from {SUPPORTED_FORMATS}")
