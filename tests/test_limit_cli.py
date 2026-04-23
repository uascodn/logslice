"""Tests for logslice.limit_cli."""
import argparse
import io
import json
import pytest

from logslice.limit_cli import build_limit_parser, run_limit


def _jsonl(*records):
    return "\n".join(json.dumps(r) for r in records) + "\n"


def _args(expr, file="-", fmt="json"):
    return argparse.Namespace(expr=expr, file=file, format=fmt)


def test_build_limit_parser_returns_parser():
    parser = build_limit_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_build_limit_parser_has_expr_and_file():
    parser = build_limit_parser()
    ns = parser.parse_args(["5"])
    assert ns.expr == "5"
    assert ns.file == "-"


def test_run_limit_simple(monkeypatch):
    data = _jsonl(*[{"i": i} for i in range(5)])
    monkeypatch.setattr("sys.stdin", io.StringIO(data))
    out = io.StringIO()
    run_limit(_args("3"), out=out)
    lines = [l for l in out.getvalue().splitlines() if l.strip()]
    assert len(lines) == 3
    assert json.loads(lines[0]) == {"i": 0}
    assert json.loads(lines[2]) == {"i": 2}


def test_run_limit_with_offset(monkeypatch):
    data = _jsonl(*[{"i": i} for i in range(10)])
    monkeypatch.setattr("sys.stdin", io.StringIO(data))
    out = io.StringIO()
    run_limit(_args("2:3"), out=out)
    lines = [l for l in out.getvalue().splitlines() if l.strip()]
    assert len(lines) == 3
    assert json.loads(lines[0]) == {"i": 2}
    assert json.loads(lines[2]) == {"i": 4}


def test_run_limit_zero_returns_nothing(monkeypatch):
    data = _jsonl(*[{"i": i} for i in range(5)])
    monkeypatch.setattr("sys.stdin", io.StringIO(data))
    out = io.StringIO()
    run_limit(_args("0"), out=out)
    assert out.getvalue().strip() == ""


def test_run_limit_bad_expr_exits(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    with pytest.raises(SystemExit) as exc_info:
        run_limit(_args("bad"))
    assert exc_info.value.code == 1


def test_run_limit_from_file(tmp_path):
    log_file = tmp_path / "test.log"
    log_file.write_text(_jsonl(*[{"i": i} for i in range(6)]))
    out = io.StringIO()
    run_limit(_args("4", file=str(log_file)), out=out)
    lines = [l for l in out.getvalue().splitlines() if l.strip()]
    assert len(lines) == 4
