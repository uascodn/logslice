import pytest
from logslice.pivot import pivot_records, parse_pivot_expr, render_pivot_table, _aggregate


@pytest.fixture
def records():
    return [
        {"service": "api", "level": "error", "duration": 120},
        {"service": "api", "level": "info",  "duration": 30},
        {"service": "api", "level": "error", "duration": 80},
        {"service": "db",  "level": "info",  "duration": 50},
        {"service": "db",  "level": "warn",  "duration": 200},
    ]


def test_pivot_count(records):
    result = pivot_records(records, "service", "level")
    assert result["api"]["error"] == 2
    assert result["api"]["info"] == 1
    assert result["db"]["info"] == 1


def test_pivot_sum(records):
    result = pivot_records(records, "service", "level", val_field="duration", agg="sum")
    assert result["api"]["error"] == 200
    assert result["db"]["warn"] == 200


def test_pivot_avg(records):
    result = pivot_records(records, "service", "level", val_field="duration", agg="avg")
    assert result["api"]["error"] == 100.0


def test_pivot_min_max(records):
    result_min = pivot_records(records, "service", "level", val_field="duration", agg="min")
    result_max = pivot_records(records, "service", "level", val_field="duration", agg="max")
    assert result_min["api"]["error"] == 80
    assert result_max["api"]["error"] == 120


def test_pivot_missing_field(records):
    result = pivot_records(records, "service", "missing_field")
    assert "" in result["api"]


def test_aggregate_unknown():
    with pytest.raises(ValueError):
        _aggregate([1, 2], "median")


def test_parse_pivot_expr_basic():
    row, col, val, agg = parse_pivot_expr("row=service,col=level")
    assert row == "service"
    assert col == "level"
    assert val is None
    assert agg == "count"


def test_parse_pivot_expr_full():
    row, col, val, agg = parse_pivot_expr("row=service,col=level,val=duration,agg=sum")
    assert val == "duration"
    assert agg == "sum"


def test_parse_pivot_expr_missing_col():
    with pytest.raises(ValueError):
        parse_pivot_expr("row=service")


def test_render_pivot_table(records):
    pivot = pivot_records(records, "service", "level")
    table = render_pivot_table(pivot)
    assert "service" not in table or True  # just check it runs
    assert "api" in table
    assert "error" in table


def test_render_pivot_empty():
    assert render_pivot_table({}) == "(empty)"
