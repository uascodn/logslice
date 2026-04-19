import pytest
from logslice.aggregate import Aggregator, parse_agg_expr, AGG_FUNCS


@pytest.fixture
def records():
    return [
        {"service": "api", "latency": "10"},
        {"service": "api", "latency": "20"},
        {"service": "db", "latency": "5"},
        {"service": "db", "latency": "bad"},
        {"service": "db"},
    ]


def test_count_no_group(records):
    agg = Aggregator(group_by=None, agg_func="count")
    for r in records:
        agg.feed(r)
    assert agg.result()["_all"] == 5


def test_count_by_service(records):
    agg = Aggregator(group_by="service", agg_func="count")
    for r in records:
        agg.feed(r)
    result = agg.result()
    assert result["api"] == 2
    assert result["db"] == 3


def test_sum_by_service(records):
    agg = Aggregator(group_by="service", agg_func="sum", field="latency")
    for r in records:
        agg.feed(r)
    result = agg.result()
    assert result["api"] == 30.0
    assert result["db"] == 5.0  # only valid numeric value


def test_avg_no_group(records):
    agg = Aggregator(group_by=None, agg_func="avg", field="latency")
    for r in records:
        agg.feed(r)
    # 10 + 20 + 5 = 35 / 3
    assert abs(agg.result()["_all"] - 35 / 3) < 1e-9


def test_min_max(records):
    agg_min = Aggregator(group_by=None, agg_func="min", field="latency")
    agg_max = Aggregator(group_by=None, agg_func="max", field="latency")
    for r in records:
        agg_min.feed(r)
        agg_max.feed(r)
    assert agg_min.result()["_all"] == 5.0
    assert agg_max.result()["_all"] == 20.0


def test_missing_field_returns_none():
    agg = Aggregator(group_by=None, agg_func="sum", field="missing")
    agg.feed({"x": 1})
    assert agg.result()["_all"] is None


def test_invalid_func_raises():
    with pytest.raises(ValueError, match="Unknown"):
        Aggregator(group_by=None, agg_func="median")


def test_non_count_without_field_raises():
    with pytest.raises(ValueError, match="Field required"):
        Aggregator(group_by=None, agg_func="sum")


def test_parse_agg_expr_count():
    agg = parse_agg_expr("count")
    assert agg.agg_func == "count"
    assert agg.field is None
    assert agg.group_by is None


def test_parse_agg_expr_avg_with_group():
    agg = parse_agg_expr("avg:latency,by:service")
    assert agg.agg_func == "avg"
    assert agg.field == "latency"
    assert agg.group_by == "service"


def test_parse_agg_expr_sum_no_group():
    agg = parse_agg_expr("sum:bytes")
    assert agg.agg_func == "sum"
    assert agg.field == "bytes"
    assert agg.group_by is None
