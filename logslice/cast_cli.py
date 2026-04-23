"""CLI entry-point for the cast sub-command.

Usage examples::

    logslice cast --cast latency:int --cast ratio:float app.log
    cat app.log | logslice cast --cast retries:int
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional, Sequence

from logslice.cast import apply_casts, parse_cast_expr
from logslice.parser import parse_line


def build_cast_parser(
    parent: Optional[argparse._SubParsersAction] = None,
) -> argparse.ArgumentParser:
    description = "Cast field values to a target type (int, float, bool, str)."
    if parent is not None:
        parser = parent.add_parser("cast", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(prog="logslice cast", description=description)

    parser.add_argument(
        "--cast",
        metavar="FIELD:TYPE",
        dest="casts",
        action="append",
        default=[],
        help="Cast expression in 'field:type' form. May be repeated.",
    )
    parser.add_argument(
        "--output",
        choices=["json", "logfmt"],
        default="json",
        help="Output format (default: json).",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Input log file (default: stdin).",
    )
    return parser


def run_cast(args: argparse.Namespace, out=None) -> None:
    """Execute the cast command using *args*."""
    if out is None:
        out = sys.stdout

    # Validate cast expressions early so we fail fast.
    try:
        for expr in args.casts:
            parse_cast_expr(expr)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    source = open(args.file) if args.file != "-" else sys.stdin
    try:
        for raw in source:
            raw = raw.rstrip("\n")
            if not raw.strip():
                continue
            record = parse_line(raw)
            if record is None:
                continue
            record = apply_casts(record, args.casts)
            if args.output == "json":
                out.write(json.dumps(record) + "\n")
            else:
                pairs = " ".join(
                    f'{k}="{v}"' if " " in str(v) else f"{k}={v}"
                    for k, v in record.items()
                )
                out.write(pairs + "\n")
    finally:
        if args.file != "-":
            source.close()


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = build_cast_parser()
    args = parser.parse_args(argv)
    run_cast(args)


if __name__ == "__main__":
    main()
