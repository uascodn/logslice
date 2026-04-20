"""Tests for logslice.diff_cli entry point."""

import io
import json
import os
import tempfile
import pytest

from logslice.diff_cli import build_diff_parser, run_diff


def _write_jsonl(records):
    """Write records to a temp file, return path."""
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    with os.fdopen(fd, "w") as fh:
        for rec in records:
            fh.write(json.dumps(rec) + "\n")
    return path


@pytest.fixture
def file_a(tmp_path):
    path = tmp_path / "a.jsonl"
    path.write_text(
        json.dumps({"level": "info", "msg": "start", "code": 0}) + "\n" +
        json.dumps({"level": "info", "msg": "done", "code": 0}) + "\n"
    )
    return str(path)


@pytest.fixture
def file_b(tmp_path):
    path = tmp_path / "b.jsonl"
    path.write_text(
        json.dumps({"level": "info", "msg": "start", "code": 0}) + "\n" +
        json.dumps({"level": "error", "msg": "done", "code": 1}) + "\n"
    )
    return str(path)


def _args(file_a, file_b, **kwargs):
    ns = build_diff_parser().parse_args([file_a, file_b])
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def test_build_diff_parser_returns_parser():
    p = build_diff_parser()
    assert p is not None


def test_run_diff_identical_returns_zero(file_a):
    args = _args(file_a, file_a, ignore_fields=[], changed_only=False, color=False)
    out = io.StringIO()
    code = run_diff(args, out=out)
    assert code == 0


def test_run_diff_changed_returns_one(file_a, file_b):
    args = _args(file_a, file_b, ignore_fields=[], changed_only=False, color=False)
    out = io.StringIO()
    code = run_diff(args, out=out)
    assert code == 1


def test_run_diff_output_contains_record_header(file_a, file_b):
    args = _args(file_a, file_b, ignore_fields=[], changed_only=False, color=False)
    out = io.StringIO()
    run_diff(args, out=out)
    assert "record 1" in out.getvalue()


def test_run_diff_changed_only_skips_unchanged(file_a, file_b):
    args = _args(file_a, file_b, ignore_fields=[], changed_only=True, color=False)
    out = io.StringIO()
    run_diff(args, out=out)
    content = out.getvalue()
    # record 1 is identical, should not appear
    assert "record 1" not in content
    assert "record 2" in content


def test_run_diff_ignore_fields(file_a, file_b):
    args = _args(file_a, file_b, ignore_fields=["level", "code"], changed_only=False, color=False)
    out = io.StringIO()
    code = run_diff(args, out=out)
    assert code == 0


def test_run_diff_extra_records_in_a(file_a, tmp_path):
    short = tmp_path / "short.jsonl"
    short.write_text(json.dumps({"level": "info", "msg": "start", "code": 0}) + "\n")
    args = _args(file_a, str(short), ignore_fields=[], changed_only=False, color=False)
    out = io.StringIO()
    code = run_diff(args, out=out)
    assert code == 1
    assert "extra" in out.getvalue()
