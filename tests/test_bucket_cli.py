"""Tests for logslice.bucket_cli."""
import argparse
import io
import json

import pytest

from logslice.bucket_cli import build_bucket_parser, run_bucket


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"expr": "level", "file": "-", "format": "summary"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _jsonl(*records) -> str:
    import json
    return "\n".join(json.dumps(r) for r in records) + "\n"


def test_build_bucket_parser_returns_parser():
    p = build_bucket_parser()
    assert isinstance(p, argparse.ArgumentParser)


def test_build_bucket_parser_has_expr_and_file():
    p = build_bucket_parser()
    args = p.parse_args(["level", "somefile.log"])
    assert args.expr == "level"
    assert args.file == "somefile.log"


def test_run_bucket_summary_output(tmp_path, monkeypatch):
    log = tmp_path / "test.log"
    log.write_text(
        _jsonl(
            {"level": "info", "msg": "hi"},
            {"level": "error", "msg": "oh no"},
            {"level": "info", "msg": "again"},
        )
    )
    out = io.StringIO()
    run_bucket(_args(expr="level", file=str(log), format="summary"), out=out)
    result = out.getvalue()
    assert "info" in result
    assert "error" in result
    assert "TOTAL" in result


def test_run_bucket_json_output(tmp_path):
    log = tmp_path / "test.log"
    log.write_text(
        _jsonl(
            {"level": "info", "msg": "a"},
            {"level": "warn", "msg": "b"},
        )
    )
    out = io.StringIO()
    run_bucket(_args(expr="level", file=str(log), format="json"), out=out)
    data = json.loads(out.getvalue())
    assert "info" in data
    assert "warn" in data


def test_run_bucket_bad_expr_exits(tmp_path):
    log = tmp_path / "empty.log"
    log.write_text("")
    with pytest.raises(SystemExit):
        run_bucket(_args(expr="", file=str(log)))


def test_run_bucket_restricted_buckets(tmp_path):
    log = tmp_path / "test.log"
    log.write_text(
        _jsonl(
            {"level": "info"},
            {"level": "debug"},
            {"level": "error"},
        )
    )
    out = io.StringIO()
    run_bucket(_args(expr="level:info,error", file=str(log), format="json"), out=out)
    data = json.loads(out.getvalue())
    assert "info" in data
    assert "error" in data
    assert "__other__" in data
    assert "debug" not in data
