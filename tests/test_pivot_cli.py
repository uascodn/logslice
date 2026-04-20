import json
import sys
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch, mock_open

import pytest

from logslice.pivot_cli import build_pivot_parser, run_pivot


LINES = [
    '{"service":"api","level":"error"}\n',
    '{"service":"api","level":"info"}\n',
    '{"service":"db","level":"error"}\n',
]


def _args(**kwargs):
    defaults = {"expr": "row=service,col=level", "file": "-", "json": False}
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_build_pivot_parser_returns_parser():
    p = build_pivot_parser()
    assert p is not None


def test_run_pivot_table_output(capsys):
    with patch("sys.stdin", StringIO("".join(LINES))):
        rc = run_pivot(_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "api" in out
    assert "error" in out


def test_run_pivot_json_output(capsys):
    with patch("sys.stdin", StringIO("".join(LINES))):
        rc = run_pivot(_args(json=True))
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "api" in data
    assert data["api"]["error"] == 1


def test_run_pivot_bad_expr(capsys):
    with patch("sys.stdin", StringIO("".join(LINES))):
        rc = run_pivot(_args(expr="row=service"))
    assert rc == 1
    err = capsys.readouterr().err
    assert "error" in err


def test_run_pivot_file_input(tmp_path, capsys):
    f = tmp_path / "test.log"
    f.write_text("".join(LINES))
    rc = run_pivot(_args(file=str(f)))
    assert rc == 0
    out = capsys.readouterr().out
    assert "db" in out


def test_run_pivot_empty_input(capsys):
    with patch("sys.stdin", StringIO("")):
        rc = run_pivot(_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "empty" in out
