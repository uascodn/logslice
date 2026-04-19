"""Log record sampling: keep every Nth record or a random fraction."""

import random
from typing import Iterable, Iterator


def sample_every_n(records: Iterable[dict], n: int) -> Iterator[dict]:
    """Yield every Nth record (1-based). n=1 yields all records."""
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")
    for i, record in enumerate(records):
        if i % n == 0:
            yield record


def sample_fraction(records: Iterable[dict], fraction: float, seed: int | None = None) -> Iterator[dict]:
    """Yield each record with probability `fraction` (0.0–1.0)."""
    if not 0.0 < fraction <= 1.0:
        raise ValueError(f"fraction must be in (0.0, 1.0], got {fraction}")
    rng = random.Random(seed)
    for record in records:
        if rng.random() < fraction:
            yield record


def parse_sample_expr(expr: str) -> dict:
    """Parse a sampling expression like '1/10' or '5%' or 'every:4'.

    Returns a dict with keys 'mode' and 'value':
      - {'mode': 'every', 'value': N}
      - {'mode': 'fraction', 'value': f}
    """
    expr = expr.strip()
    if expr.startswith("every:"):
        n = int(expr[len("every:"):])
        return {"mode": "every", "value": n}
    if "/" in expr:
        num, denom = expr.split("/", 1)
        fraction = int(num.strip()) / int(denom.strip())
        return {"mode": "fraction", "value": fraction}
    if expr.endswith("%"):
        fraction = float(expr[:-1]) / 100.0
        return {"mode": "fraction", "value": fraction}
    # bare integer → every N
    return {"mode": "every", "value": int(expr)}


def apply_sampling(records: Iterable[dict], expr: str, seed: int | None = None) -> Iterator[dict]:
    """Parse expr and apply the appropriate sampling strategy."""
    spec = parse_sample_expr(expr)
    if spec["mode"] == "every":
        return sample_every_n(records, spec["value"])
    return sample_fraction(records, spec["value"], seed=seed)
