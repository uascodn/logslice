"""Tests for logslice.highlight module."""

import pytest
from logslice.highlight import (
    colorize_level,
    highlight_field,
    highlight_pattern,
    highlight_record,
    ANSI_RESET,
    ANSI_BOLD,
)


def test_colorize_level_error():
    result = colorize_level("error")
    assert "error" in result
    assert ANSI_RESET in result


def test_colorize_level_case_insensitive():
    upper = colorize_level("ERROR")
    lower = colorize_level("error")
    # Both should be colored (contain reset)
    assert ANSI_RESET in upper
    assert ANSI_RESET in lower


def test_colorize_level_unknown_returns_plain():
    result = colorize_level("unknown")
    assert result == "unknown"


def test_colorize_level_warning_alias():
    result = colorize_level("warning")
    assert ANSI_RESET in result


def test_highlight_field_contains_key_and_value():
    result = highlight_field("service", "auth")
    assert "service" in result
    assert "auth" in result
    assert ANSI_BOLD in result


def test_highlight_pattern_wraps_match():
    result = highlight_pattern("hello world", "world")
    assert "world" in result
    assert ANSI_RESET in result


def test_highlight_pattern_case_insensitive():
    result = highlight_pattern("Hello World", "hello")
    assert ANSI_RESET in result


def test_highlight_pattern_empty_pattern_returns_original():
    text = "no change here"
    result = highlight_pattern(text, "")
    assert result == text


def test_highlight_pattern_invalid_regex_returns_original():
    text = "some text"
    result = highlight_pattern(text, "[invalid")
    assert result == text


def test_highlight_record_contains_all_keys():
    record = {"level": "info", "msg": "started", "service": "api"}
    result = highlight_record(record)
    assert "level" in result
    assert "msg" in result
    assert "service" in result


def test_highlight_record_level_colored():
    record = {"level": "error", "msg": "boom"}
    result = highlight_record(record)
    assert ANSI_RESET in result


def test_highlight_record_search_highlighted():
    record = {"msg": "connection refused", "level": "error"}
    result = highlight_record(record, search="refused")
    assert "refused" in result
    assert ANSI_RESET in result
