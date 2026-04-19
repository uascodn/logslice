"""Tests for logslice.sampling."""

import pytest
from logslice.sampling import (
    sample_every_n,
    sample_fraction,
    parse_sample_expr,
    apply_sampling,
)


def records(n=10):
    return [{"i": i, "msg": f"line {i}"} for i in range(n)]


def test_sample_every_n_all():
    result = list(sample_every_n(records(6), 1))
    assert len(result) == 6


def test_sample_every_n_half():
    result = list(sample_every_n(records(10), 2))
    assert [r["i"] for r in result] == [0, 2, 4, 6, 8]


def test_sample_every_n_invalid():
    with pytest.raises(ValueError):
        list(sample_every_n(records(), 0))


def test_sample_fraction_seed_deterministic():
    r = records(100)
    a = list(sample_fraction(r, 0.5, seed=42))
    b = list(sample_fraction(r, 0.5, seed=42))
    assert a == b


def test_sample_fraction_all():
    result = list(sample_fraction(records(20), 1.0, seed=0))
    assert len(result) == 20


def test_sample_fraction_invalid_zero():
    with pytest.raises(ValueError):
        list(sample_fraction(records(), 0.0))


def test_sample_fraction_invalid_over_one():
    with pytest.raises(ValueError):
        list(sample_fraction(records(), 1.5))


def test_parse_sample_expr_every_colon():
    assert parse_sample_expr("every:5") == {"mode": "every", "value": 5}


def test_parse_sample_expr_fraction_slash():
    spec = parse_sample_expr("1/4")
    assert spec["mode"] == "fraction"
    assert abs(spec["value"] - 0.25) < 1e-9


def test_parse_sample_expr_percent():
    spec = parse_sample_expr("10%")
    assert spec["mode"] == "fraction"
    assert abs(spec["value"] - 0.10) < 1e-9


def test_parse_sample_expr_bare_int():
    assert parse_sample_expr("3") == {"mode": "every", "value": 3}


def test_apply_sampling_every():
    result = list(apply_sampling(records(9), "every:3"))
    assert [r["i"] for r in result] == [0, 3, 6]


def test_apply_sampling_fraction():
    result = list(apply_sampling(records(100), "50%", seed=7))
    assert 30 < len(result) < 70
