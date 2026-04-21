"""Tests for logslice.annotate_cli."""
from __future__ import annotations

import io
import json
import pytest
from unittest.mock import patch, MagicMock

from logslice.annotate_cli import build_annotate_parser, run_annotate


def _args(**kwargs):
    defaults = {
        "file": "-",
        "annotations": [],
        "index": None,
        "index_start": 0,
        "format": "json",
    }
    defaults.update(kwargs)
    return MagicMock(**defaults)


def _jsonl(*records):
    return io.StringIO("\n".join(json.dumps(r) for r in records) + "\n")


def test_build_annotate_parser_returns_parser():
    p = build_annotate_parser()
    assert p is not None
    args = p.parse_args([])
    assert args.format == "json"


def test_run_annotate_static_field():
    lines = _jsonl({"level": "info", "msg": "hi"})
    out = io.StringIO()
    args = _args(annotations=["env=prod"])
    with patch("sys.stdin", lines):
        run_annotate(args, out=out)
    result = json.loads(out.getvalue().strip())
    assert result["env"] == "prod"
    assert result["level"] == "info"


def test_run_annotate_index():
    lines = _jsonl({"msg": "a"}, {"msg": "b"}, {"msg": "c"})
    out = io.StringIO()
    args = _args(index="seq", index_start=1)
    with patch("sys.stdin", lines):
        run_annotate(args, out=out)
    rows = [json.loads(l) for l in out.getvalue().strip().splitlines()]
    assert [r["seq"] for r in rows] == [1, 2, 3]


def test_run_annotate_derived():
    lines = _jsonl({"service": "api", "level": "info"})
    out = io.StringIO()
    args = _args(annotations=["tag={service}-{level}"])
    with patch("sys.stdin", lines):
        run_annotate(args, out=out)
    result = json.loads(out.getvalue().strip())
    assert result["tag"] == "api-info"


def test_run_annotate_multiple_expressions():
    lines = _jsonl({"service": "db"})
    out = io.StringIO()
    args = _args(annotations=["env=test", "owner=team-a"])
    with patch("sys.stdin", lines):
        run_annotate(args, out=out)
    result = json.loads(out.getvalue().strip())
    assert result["env"] == "test"
    assert result["owner"] == "team-a"


def test_run_annotate_bad_expr_exits(capsys):
    lines = _jsonl({"msg": "x"})
    args = _args(annotations=["badexpr"])
    with patch("sys.stdin", lines):
        with pytest.raises(SystemExit) as exc_info:
            run_annotate(args)
    assert exc_info.value.code == 1


def test_run_annotate_skips_empty_lines():
    lines = io.StringIO('{"msg": "ok"}\n\n{"msg": "also ok"}\n')
    out = io.StringIO()
    args = _args(annotations=["env=x"])
    with patch("sys.stdin", lines):
        run_annotate(args, out=out)
    rows = [json.loads(l) for l in out.getvalue().strip().splitlines()]
    assert len(rows) == 2
