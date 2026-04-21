"""CLI entry point for the histogram sub-command."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from logslice.histogram import build_histogram, parse_bucket_expr, render_histogram
from logslice.parser import parse_line


def build_histogram_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice histogram",
        description="Display a time-bucketed histogram of log records.",
    )
    p.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Input log file (default: stdin)",
    )
    p.add_argument(
        "--bucket",
        default="1m",
        metavar="SIZE",
        help="Bucket size, e.g. 30s, 5m, 1h (default: 1m)",
    )
    p.add_argument(
        "--ts-field",
        default="timestamp",
        metavar="FIELD",
        help="Field to use as timestamp (default: timestamp)",
    )
    p.add_argument(
        "--count-field",
        default=None,
        metavar="FIELD",
        help="Sum this numeric field instead of counting records",
    )
    p.add_argument(
        "--json",
        dest="output_json",
        action="store_true",
        help="Output histogram as JSON instead of ASCII chart",
    )
    p.add_argument(
        "--bar-width",
        type=int,
        default=40,
        metavar="",
        help="Width of ASCII bars (default: 40)",
    )
    return p


def run_histogram(args: argparse.Namespace, out=None) -> None:
    if out is None:
        out = sys.stdout

    try:
        bucket_size = parse_bucket_expr(args.bucket)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.file == "-":
        lines = sys.stdin
    else:
        lines = open(args.file)

    records = [r for line in lines if (r := parse_line(line)) is not None]

    histogram = build_histogram(
        records,
        bucket_size,
        ts_field=args.ts_field,
        count_field=args.count_field,
    )

    if args.output_json:
        payload = [
            {"bucket": bucket.isoformat(), "count": count}
            for bucket, count in histogram
        ]
        print(json.dumps(payload), file=out)
    else:
        print(render_histogram(histogram, bar_width=args.bar_width), file=out)


def main() -> None:
    parser = build_histogram_parser()
    args = parser.parse_args()
    run_histogram(args)


if __name__ == "__main__":
    main()
