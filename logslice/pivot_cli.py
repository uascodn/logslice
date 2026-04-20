"""CLI sub-command: pivot — group log records into a pivot table."""
import argparse
import sys
from typing import List

from logslice.parser import parse_line
from logslice.pivot import parse_pivot_expr, pivot_records, render_pivot_table


def build_pivot_parser(subparsers=None):
    desc = "Pivot log records by two fields and aggregate a third."
    if subparsers is not None:
        p = subparsers.add_parser("pivot", help=desc, description=desc)
    else:
        p = argparse.ArgumentParser(prog="logslice pivot", description=desc)
    p.add_argument(
        "expr",
        help="Pivot expression: row=<field>,col=<field>[,val=<field>][,agg=count|sum|avg|min|max]",
    )
    p.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Input log file (default: stdin)",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Output raw pivot dict as JSON instead of table",
    )
    return p


def run_pivot(args) -> int:
    import json

    try:
        row, col, val, agg = parse_pivot_expr(args.expr)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    records: List = []
    src = open(args.file) if args.file != "-" else sys.stdin
    try:
        for line in src:
            rec = parse_line(line)
            if rec is not None:
                records.append(rec)
    finally:
        if args.file != "-":
            src.close()

    pivot = pivot_records(records, row, col, val_field=val, agg=agg)

    if args.json:
        print(json.dumps(pivot, indent=2))
    else:
        print(render_pivot_table(pivot))
    return 0


def main():
    parser = build_pivot_parser()
    args = parser.parse_args()
    sys.exit(run_pivot(args))


if __name__ == "__main__":
    main()
