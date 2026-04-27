"""Integration tests for the label feature end-to-end."""

from __future__ import annotations

import json

from logslice.label import apply_labels, parse_label_expr
from logslice.parser import parse_line


def _parse_records(lines: list[str]) -> list[dict]:
    result = []
    for line in lines:
        rec = parse_line(line.strip())
        if rec:
            result.append(rec)
    return result


def test_integration_label_from_json_lines():
    raw = [
        '{"level": "error", "service": "api"}',
        '{"level": "warn",  "service": "db"}',
        '{"level": "info",  "service": "api"}',
        '{"level": "debug", "service": "db"}',
    ]
    records = _parse_records(raw)
    src, dst, rules, default = parse_label_expr(
        "level->severity:error=critical,warn=warning,info=info,*=trace"
    )
    labeled = apply_labels(records, src, dst, rules, default)
    severities = [r["severity"] for r in labeled]
    assert severities == ["critical", "warning", "info", "trace"]


def test_integration_label_preserves_all_other_fields():
    raw = ['{"level": "error", "msg": "oops", "ts": "2024-01-01T00:00:00Z"}']
    records = _parse_records(raw)
    src, dst, rules, default = parse_label_expr("level->severity:error=critical")
    labeled = apply_labels(records, src, dst, rules, default)
    rec = labeled[0]
    assert rec["msg"] == "oops"
    assert rec["ts"] == "2024-01-01T00:00:00Z"
    assert rec["level"] == "error"
    assert rec["severity"] == "critical"


def test_integration_label_missing_source_field_with_default():
    raw = ['{"msg": "no level here"}']
    records = _parse_records(raw)
    src, dst, rules, default = parse_label_expr("level->severity:error=critical,*=unknown")
    labeled = apply_labels(records, src, dst, rules, default)
    assert labeled[0]["severity"] == "unknown"


def test_integration_label_roundtrip_json():
    raw = ['{"level": "warn", "code": 503}']
    records = _parse_records(raw)
    src, dst, rules, default = parse_label_expr("level->severity:warn=warning")
    labeled = apply_labels(records, src, dst, rules, default)
    serialized = json.dumps(labeled[0])
    back = json.loads(serialized)
    assert back["severity"] == "warning"
    assert back["code"] == 503
