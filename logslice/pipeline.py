"""Pipeline builder: composes parsing, filtering, transforms, and output."""
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional

from logslice.parser import parse_line
from logslice.filter import apply_filters, parse_filter_expr
from logslice.timerange import in_time_range, parse_time_range, extract_timestamp
from logslice.transform import apply_transforms, parse_transform_expr
from logslice.sampling import apply_sampling, parse_sample_expr
from logslice.dedupe import dedupe_records, dedupe_consecutive
from logslice.truncate import truncate_fields, parse_truncate_expr
from logslice.flatten import flatten_record, parse_flatten_expr
from logslice.output import format_record


def build_pipeline(args: Any) -> Callable[[Iterable[str]], Iterator[str]]:
    """Build a processing pipeline from parsed CLI args."""
    filters = [parse_filter_expr(e) for e in (getattr(args, "filter", None) or [])]
    transforms = [parse_transform_expr(e) for e in (getattr(args, "transform", None) or [])]
    time_range = parse_time_range(getattr(args, "time_range", None))
    sample_expr = getattr(args, "sample", None)
    sample_opts = parse_sample_expr(sample_expr) if sample_expr else None
    dedupe = getattr(args, "dedupe", False)
    dedupe_consec = getattr(args, "dedupe_consecutive", False)
    truncate_exprs = [parse_truncate_expr(e) for e in (getattr(args, "truncate", None) or [])]
    flatten_expr = getattr(args, "flatten", None)
    flatten_opts = parse_flatten_expr(flatten_expr) if flatten_expr is not None else None
    fmt = getattr(args, "output_format", "json")

    def pipeline(lines: Iterable[str]) -> Iterator[str]:
        records: Iterable[Dict[str, Any]] = (
            r for line in lines if (r := parse_line(line)) is not None
        )

        if time_range[0] or time_range[1]:
            start, end = time_range
            records = (
                r for r in records
                if in_time_range(extract_timestamp(r), start, end)
            )

        if filters:
            records = apply_filters(records, filters)

        if flatten_opts is not None:
            records = (flatten_record(r, **flatten_opts) for r in records)

        if transforms:
            records = apply_transforms(records, transforms)

        if truncate_exprs:
            for opts in truncate_exprs:
                field = opts.pop("field", None)
                records = (truncate_fields(r, [field], **opts) if field else records for r in records)
                if field:
                    opts["field"] = field

        if sample_opts:
            records = apply_sampling(records, sample_opts)

        if dedupe:
            records = dedupe_records(records)
        elif dedupe_consec:
            records = dedupe_consecutive(records)

        for record in records:
            yield format_record(record, fmt)

    return pipeline


def run_pipeline(args: Any, lines: Iterable[str]) -> List[str]:
    """Run the pipeline and collect output lines."""
    pipeline = build_pipeline(args)
    return list(pipeline(lines))
