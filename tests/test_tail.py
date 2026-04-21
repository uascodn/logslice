"""Tests for logslice.tail."""

from __future__ import annotations

import os
import tempfile
import threading
import time

import pytest

from logslice.tail import (
    follow_file,
    last_n_lines,
    parse_tail_expr,
    tail_records,
)


@pytest.fixture()
def tmp_log(tmp_path):
    """Write a small log file and return its path."""
    p = tmp_path / "test.log"
    lines = [f"line {i}" for i in range(1, 11)]  # line 1 … line 10
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(p)


# ---------------------------------------------------------------------------
# last_n_lines
# ---------------------------------------------------------------------------

def test_last_n_lines_fewer_than_n(tmp_log):
    result = last_n_lines(tmp_log, 20)
    assert len(result) == 10
    assert result[0] == "line 1"
    assert result[-1] == "line 10"


def test_last_n_lines_exact(tmp_log):
    result = last_n_lines(tmp_log, 10)
    assert len(result) == 10


def test_last_n_lines_partial(tmp_log):
    result = last_n_lines(tmp_log, 3)
    assert result == ["line 8", "line 9", "line 10"]


def test_last_n_lines_zero(tmp_log):
    assert last_n_lines(tmp_log, 0) == []


def test_last_n_lines_negative(tmp_log):
    assert last_n_lines(tmp_log, -5) == []


# ---------------------------------------------------------------------------
# tail_records
# ---------------------------------------------------------------------------

def test_tail_records_returns_iterable(tmp_log):
    result = list(tail_records(tmp_log, 5))
    assert len(result) == 5
    assert result[-1] == "line 10"


# ---------------------------------------------------------------------------
# parse_tail_expr
# ---------------------------------------------------------------------------

def test_parse_tail_expr_valid():
    assert parse_tail_expr("50") == 50


def test_parse_tail_expr_one():
    assert parse_tail_expr("1") == 1


def test_parse_tail_expr_non_numeric():
    with pytest.raises(ValueError, match="integer"):
        parse_tail_expr("abc")


def test_parse_tail_expr_zero():
    with pytest.raises(ValueError, match=">= 1"):
        parse_tail_expr("0")


def test_parse_tail_expr_negative():
    with pytest.raises(ValueError, match=">= 1"):
        parse_tail_expr("-10")


# ---------------------------------------------------------------------------
# follow_file  (basic: new lines are yielded)
# ---------------------------------------------------------------------------

def test_follow_file_yields_new_lines(tmp_path):
    p = tmp_path / "follow.log"
    p.write_text("", encoding="utf-8")

    collected: list[str] = []

    def _writer():
        time.sleep(0.1)
        with open(str(p), "a", encoding="utf-8") as fh:
            fh.write("hello\n")
            fh.flush()
        time.sleep(0.1)
        with open(str(p), "a", encoding="utf-8") as fh:
            fh.write("world\n")
            fh.flush()

    def _reader():
        gen = follow_file(str(p), poll_interval=0.05)
        for _ in range(2):
            collected.append(next(gen))

    t_write = threading.Thread(target=_writer, daemon=True)
    t_read = threading.Thread(target=_reader, daemon=True)
    t_write.start()
    t_read.start()
    t_read.join(timeout=3)

    assert collected == ["hello", "world"]
