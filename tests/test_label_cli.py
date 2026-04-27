"""Tests for logslice.label_cli."""

from __future__ import annotations

import io
import json
import textwrap

import pytest

from logslice.label_cli import build_label_parser, run_label


def _args(**kwargs):
    defaults = {"expr": "level->severity:error=critical,*=other", "file": "-", "output": "json"}
    defaults.update(kwargs)

    class NS:
        pass

    ns = NS()
    for k, v in defaults.items():
        setattr(ns, k, v)
    return ns


def _jsonl(*records):
    return io.StringIO("".join(json.dumps(r) + "\n" for r in records))


def test_build_label_parser_returns_parser():
    parser = build_label_parser()
    assert parser is not None


def test_build_label_parser_has_expr_and_file():
    parser = build_label_parser()
    args = parser.parse_args(["level->severity:error=critical", "-"])
    assert args.expr == "level->severity:error=critical"
    assert args.file == "-"


def test_run_label_adds_field(monkeypatch):
    records = [{"level": "error", "msg": "boom"}, {"level": "info", "msg": "ok"}]
    monkeypatch.setattr("sys.stdin", _jsonl(*records))
    out = io.StringIO()
    run_label(_args(), out=out)
    lines = [l for l in out.getvalue().splitlines() if l]
    assert json.loads(lines[0])["severity"] == "critical"
    assert json.loads(lines[1])["severity"] == "other"


def test_run_label_default_applied(monkeypatch):
    records = [{"level": "debug"}]
    monkeypatch.setattr("sys.stdin", _jsonl(*records))
    out = io.StringIO()
    run_label(_args(expr="level->severity:error=critical,*=other"), out=out)
    result = json.loads(out.getvalue().strip())
    assert result["severity"] == "other"


def test_run_label_logfmt_output(monkeypatch):
    records = [{"level": "error"}]
    monkeypatch.setattr("sys.stdin", _jsonl(*records))
    out = io.StringIO()
    run_label(_args(output="logfmt"), out=out)
    assert "severity=critical" in out.getvalue()


def test_run_label_bad_expr_exits(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO())
    with pytest.raises(SystemExit):
        run_label(_args(expr="bad_expr"))


def test_run_label_skips_empty_lines(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("\n\n"))
    out = io.StringIO()
    run_label(_args(), out=out)
    assert out.getvalue() == ""
