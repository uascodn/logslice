"""Integration helpers: apply masking/redaction as an enrichment step in the pipeline."""

from typing import Callable
from logslice.mask import mask_fields, redact_patterns, parse_mask_expr


def make_mask_enricher(exprs: list[str]) -> Callable[[dict], dict]:
    """Return an enricher function that masks specified fields.

    Each expression is parsed via parse_mask_expr, e.g. 'password:keep=2'.
    """
    parsed = [parse_mask_expr(e) for e in exprs]

    def enricher(record: dict) -> dict:
        for p in parsed:
            record = mask_fields(record, [p["field"]], char=p["char"], keep=p["keep"])
        return record

    return enricher


def make_redact_enricher(pattern_names: list[str] | None = None) -> Callable[[dict], dict]:
    """Return an enricher function that redacts known sensitive patterns.

    pattern_names: subset of ['email', 'ipv4', 'token'], or None for all.
    """
    def enricher(record: dict) -> dict:
        return redact_patterns(record, pattern_names=pattern_names)

    return enricher


def apply_mask_steps(record: dict, mask_exprs: list[str], redact: list[str] | None = None) -> dict:
    """Convenience: apply masking and optional pattern redaction to a single record."""
    if mask_exprs:
        enricher = make_mask_enricher(mask_exprs)
        record = enricher(record)
    if redact is not None:
        record = redact_patterns(record, pattern_names=redact or None)
    return record
