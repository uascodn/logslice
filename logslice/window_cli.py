"""CLI entry point for window aggregation subcommand."""

import argparse
import json
import sys
from collections import Counter
from typing import Dict, List

from logslice.parser import parse_line
from logslice.window import aggregate_window, parse_window_expr, tumbling_windows


def _count_agg(records: List[Dict]) -> Dict:
    return {"count": len(records)}


def _level_count_agg(records: List[Dict]) -> Dict:
    counter: Counter = Counter()
    for r in records:
        level = r.get("level", "unknown")
        counter[str(level)] += 1
    return {"count": len(records), "levels": dict(counter)}


AGG_FUNCTIONS = {
    "count": _count_agg,
    "level_count": _level_count_agg,
}


def build_window_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice window",
        description="Aggregate log records into tumbling time windows.",
    )
    p.add_argument("file", nargs="?", default="-", help="Input file (default: stdin)")
    p.add_argument(
        "--size",
        required=True,
        metavar="DURATION",
        help="Window size, e.g. 1m, 30s, 2h",
    )
    p.add_argument(
        "--agg",
        default="count",
        choices=list(AGG_FUNCTIONS),
        help="Aggregation function (default: count)",
    )
    p.add_argument(
        "--ts-field",
        default="timestamp",
        metavar="FIELD",
        help="Field containing the timestamp (default: timestamp)",
    )
    return p


def run_window(args: argparse.Namespace, out=None) -> None:
    if out is None:
        out = sys.stdout

    try:
        window_size = parse_window_expr(args.size)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    agg_fn = AGG_FUNCTIONS[args.agg]

    src = open(args.file) if args.file != "-" else sys.stdin
    try:
        records = (r for line in src if (r := parse_line(line)) is not None)
        for window in tumbling_windows(records, window_size, ts_field=args.ts_field):
            summary = aggregate_window(window, agg_fn)
            out.write(json.dumps(summary) + "\n")
    finally:
        if args.file != "-":
            src.close()


def main() -> None:  # pragma: no cover
    parser = build_window_parser()
    args = parser.parse_args()
    run_window(args)


if __name__ == "__main__":  # pragma: no cover
    main()
