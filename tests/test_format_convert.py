"""Tests for logslice.format_convert and format_convert_cli."""
from __future__ import annotations

import argparse
import io
import json

import pytest

from logslice.format_convert import (
    convert_record,
    parse_format_expr,
    record_to_csv,
    record_to_json,
    record_to_logfmt,
    records_to_csv,
)
from logslice.format_convert_cli import build_format_convert_parser, run_format_convert


# ---------------------------------------------------------------------------
# record_to_json
# ---------------------------------------------------------------------------

def test_record_to_json_roundtrip():
    rec = {"level": "info", "msg": "hello", "code": 42}
    assert json.loads(record_to_json(rec)) == rec


# ---------------------------------------------------------------------------
# record_to_logfmt
# ---------------------------------------------------------------------------

def test_record_to_logfmt_simple():
    result = record_to_logfmt({"level": "info", "msg": "ok"})
    assert "level=info" in result
    assert "msg=ok" in result


def test_record_to_logfmt_quotes_spaces():
    result = record_to_logfmt({"msg": "hello world"})
    assert 'msg="hello world"' in result


def test_record_to_logfmt_quotes_equals():
    result = record_to_logfmt({"expr": "a=b"})
    assert 'expr="a=b"' in result


# ---------------------------------------------------------------------------
# records_to_csv
# ---------------------------------------------------------------------------

def test_records_to_csv_header_and_rows():
    recs = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
    rows = list(records_to_csv(recs))
    assert rows[0].strip() == "a,b"
    assert rows[1].strip() == "1,2"
    assert rows[2].strip() == "3,4"


def test_records_to_csv_custom_columns():
    recs = [{"a": 1, "b": 2, "c": 3}]
    rows = list(records_to_csv(recs, columns=["b", "a"]))
    assert rows[0].strip() == "b,a"
    assert rows[1].strip() == "2,1"


def test_records_to_csv_tsv_delimiter():
    recs = [{"x": "foo", "y": "bar"}]
    rows = list(records_to_csv(recs, delimiter="\t"))
    assert "\t" in rows[0]


def test_records_to_csv_empty():
    assert list(records_to_csv([])) == []


# ---------------------------------------------------------------------------
# parse_format_expr
# ---------------------------------------------------------------------------

def test_parse_format_expr_json():
    assert parse_format_expr("json") == {"format": "json", "columns": None}


def test_parse_format_expr_csv_with_columns():
    spec = parse_format_expr("csv:level,msg")
    assert spec["format"] == "csv"
    assert spec["columns"] == ["level", "msg"]


def test_parse_format_expr_invalid_raises():
    with pytest.raises(ValueError, match="Unsupported format"):
        parse_format_expr("xml")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _args(**kwargs) -> argparse.Namespace:
    defaults = {"expr": "json", "file": "-"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _jsonl(*records) -> io.StringIO:
    return io.StringIO("\n".join(json.dumps(r) for r in records) + "\n")


def test_build_format_convert_parser_returns_parser():
    p = build_format_convert_parser()
    assert isinstance(p, argparse.ArgumentParser)


def test_run_convert_json_passthrough(monkeypatch):
    recs = [{"level": "info", "msg": "hi"}]
    monkeypatch.setattr("sys.stdin", _jsonl(*recs))
    out = io.StringIO()
    rc = run_format_convert(_args(expr="json"), out=out)
    assert rc == 0
    assert json.loads(out.getvalue().strip()) == recs[0]


def test_run_convert_logfmt(monkeypatch):
    monkeypatch.setattr("sys.stdin", _jsonl({"level": "warn", "msg": "oops"}))
    out = io.StringIO()
    rc = run_format_convert(_args(expr="logfmt"), out=out)
    assert rc == 0
    assert "level=warn" in out.getvalue()


def test_run_convert_bad_expr():
    out = io.StringIO()
    err = io.StringIO()
    rc = run_format_convert(_args(expr="yaml"), out=out, err=err)
    assert rc == 1
    assert "error" in err.getvalue()
