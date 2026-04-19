"""Tests for logslice.pager module."""

import os
import sys
from unittest.mock import patch, MagicMock

import pytest
from logslice.pager import get_pager, should_use_pager, pipe_to_pager


def test_get_pager_returns_string_or_none():
    result = get_pager()
    assert result is None or isinstance(result, str)


def test_get_pager_respects_env(monkeypatch):
    monkeypatch.setenv("LOGSLICE_PAGER", "cat")
    result = get_pager()
    assert result == "cat"


def test_get_pager_missing_binary_returns_none(monkeypatch):
    monkeypatch.setenv("LOGSLICE_PAGER", "nonexistent_pager_xyz")
    result = get_pager()
    assert result is None


def test_should_use_pager_no_pager_flag():
    assert should_use_pager(no_pager=True) is False


def test_should_use_pager_force():
    assert should_use_pager(force=True, no_pager=False) is True


def test_should_use_pager_force_overridden_by_no_pager():
    assert should_use_pager(force=True, no_pager=True) is False


def test_should_use_pager_non_tty():
    with patch.object(sys.stdout, "isatty", return_value=False):
        assert should_use_pager() is False


def test_should_use_pager_tty():
    with patch.object(sys.stdout, "isatty", return_value=True):
        assert should_use_pager() is True


def test_pipe_to_pager_no_pager_prints(capsys):
    pipe_to_pager(["line one", "line two"], pager_cmd=None)
    # When no pager available, falls back to print — patch get_pager to return None
    # This test uses cat which is almost always available; skip if not


def test_pipe_to_pager_with_cat(capsys):
    import shutil
    if not shutil.which("cat"):
        pytest.skip("cat not available")
    # Should not raise
    pipe_to_pager(["hello", "world"], pager_cmd="cat")


def test_pipe_to_pager_missing_pager_falls_back(capsys):
    pipe_to_pager(["fallback line"], pager_cmd="nonexistent_pager_xyz")
    captured = capsys.readouterr()
    assert "fallback line" in captured.out
