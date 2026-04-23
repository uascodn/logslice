"""CLI sub-command for limiting and offsetting log record output."""
from __future__ import annotations

import argparse
import json
import sys

from logslice.limit import apply_limit, parse_limit_expr
from logslice.parser import parse_line
from logslice.output import format_record


def build_limit_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Output at most N records, optionally skipping the first M."
    if subparsers is not None:
        parser = subparsers.add_parser("limit", description=description, help=description)
    else:
        parser = argparse.ArgumentParser(prog="logslice limit", description=description)

    parser.add_argument(
        "expr",
        metavar="EXPR",
        help="Limit expression: 'N' or 'offset:N' (e.g. '100' or '50:100').",
    )
    parser.add_argument(
        "file",
        metavar="FILE",
        nargs="?",
        default="-",
        help="Input log file (default: stdin).",
    )
    parser.add_argument(
        "--format",
        choices=["json", "logfmt", "pretty"],
        default="json",
        help="Output format (default: json).",
    )
    return parser


def run_limit(args: argparse.Namespace, out=None) -> None:
    if out is None:
        out = sys.stdout

    try:
        params = parse_limit_expr(args.expr)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    src = sys.stdin if args.file == "-" else open(args.file)
    try:
        raw_records = (parse_line(line) for line in src if line.strip())
        valid_records = (r for r in raw_records if r is not None)
        for record in apply_limit(valid_records, args.expr):
            out.write(format_record(record, fmt=args.format) + "\n")
    finally:
        if args.file != "-":
            src.close()


def main() -> None:  # pragma: no cover
    parser = build_limit_parser()
    args = parser.parse_args()
    run_limit(args)


if __name__ == "__main__":  # pragma: no cover
    main()
