"""CLI entry-point for the bucket sub-command."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from logslice.bucket import bucket_records, parse_bucket_field_expr, render_bucket_summary
from logslice.parser import parse_line


def build_bucket_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Group log records into discrete field-value buckets."
    if subparsers is not None:
        p = subparsers.add_parser("bucket", description=description)
    else:
        p = argparse.ArgumentParser(prog="logslice bucket", description=description)
    p.add_argument(
        "expr",
        help="Field expression: 'field' or 'field:v1,v2' to restrict buckets.",
    )
    p.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Input log file (default: stdin).",
    )
    p.add_argument(
        "--format",
        choices=["summary", "json"],
        default="summary",
        help="Output format (default: summary).",
    )
    return p


def run_bucket(args: argparse.Namespace, out=None) -> None:
    if out is None:
        out = sys.stdout

    try:
        field, buckets = parse_bucket_field_expr(args.expr)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    src = sys.stdin if args.file == "-" else open(args.file)
    try:
        records = [parse_line(line) for line in src if line.strip()]
        records = [r for r in records if r is not None]
    finally:
        if args.file != "-":
            src.close()

    groups = bucket_records(records, field, buckets)

    if args.format == "json":
        payload = {k: v for k, v in groups.items()}
        print(json.dumps(payload, default=str), file=out)
    else:
        print(render_bucket_summary(groups, field), file=out)


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_bucket_parser()
    args = parser.parse_args(argv)
    run_bucket(args)


if __name__ == "__main__":
    main()
