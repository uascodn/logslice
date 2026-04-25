"""CLI entry-point for the compute sub-command."""

import argparse
import json
import sys
from typing import List, Optional

from logslice.parser import parse_line
from logslice.compute import parse_compute_expr, apply_computes
from logslice.output import format_record


def build_compute_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:
    description = "Add computed numeric fields derived from existing field values."
    if parent is not None:
        p = parent.add_parser("compute", help=description, description=description)
    else:
        p = argparse.ArgumentParser(prog="logslice compute", description=description)
    p.add_argument(
        "expr",
        nargs="+",
        metavar="FIELD=EXPR",
        help="One or more compute expressions, e.g. latency_s=latency_ms/1000",
    )
    p.add_argument(
        "file",
        nargs="?",
        default="-",
        metavar="FILE",
        help="Input log file (default: stdin)",
    )
    p.add_argument(
        "--format",
        choices=["json", "logfmt", "pretty"],
        default="json",
        help="Output format (default: json)",
    )
    p.add_argument(
        "--skip-errors",
        action="store_true",
        help="Skip lines where any compute expression fails instead of omitting the field",
    )
    return p


def run_compute(args: argparse.Namespace, out=None) -> None:
    if out is None:
        out = sys.stdout

    try:
        parsed_exprs = [parse_compute_expr(e) for e in args.expr]
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    source = args.file if hasattr(args, "file") else "-"
    fh = open(source) if source != "-" else sys.stdin

    try:
        for raw in fh:
            raw = raw.rstrip("\n")
            if not raw.strip():
                continue
            record = parse_line(raw)
            if record is None:
                continue
            enriched = apply_computes(record, parsed_exprs)
            print(format_record(enriched, fmt=args.format), file=out)
    finally:
        if source != "-":
            fh.close()


def main() -> None:
    parser = build_compute_parser()
    args = parser.parse_args()
    run_compute(args)


if __name__ == "__main__":
    main()
