"""CLI entry point for the compare subcommand."""
from __future__ import annotations

import argparse
import sys
from typing import IO

from logslice.compare import compare_streams
from logslice.compare_report import render_compare_report


def build_compare_parser(subparsers=None) -> argparse.ArgumentParser:
    kwargs = dict(
        description="Compare two structured log files by key fields."
    )
    if subparsers is not None:
        parser = subparsers.add_parser("compare", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument("file_a", help="First log file (or '-' for stdin)")
    parser.add_argument("file_b", help="Second log file")
    parser.add_argument(
        "--key",
        dest="key_fields",
        default="id",
        help="Comma-separated fields to use as record key (default: id)",
    )
    parser.add_argument(
        "--fields",
        dest="compare_fields",
        default=None,
        help="Comma-separated fields to compare (default: all)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output diff records as JSON instead of report",
    )
    return parser


def _open(path: str) -> IO[str]:
    if path == "-":
        return sys.stdin
    return open(path)


def run_compare(args: argparse.Namespace) -> int:
    import json

    key_fields = [f.strip() for f in args.key_fields.split(",")]
    compare_fields = (
        [f.strip() for f in args.compare_fields.split(",")]
        if args.compare_fields
        else None
    )

    with _open(args.file_a) as fa, _open(args.file_b) as fb:
        diffs = list(compare_streams(fa, fb, key_fields, compare_fields))

    if args.json:
        for d in diffs:
            print(json.dumps(d))
    else:
        print(render_compare_report(diffs))

    changed_or_missing = sum(
        1 for d in diffs if d["status"] in ("only_in_a", "only_in_b", "changed")
    )
    return 1 if changed_or_missing else 0


if __name__ == "__main__":
    _parser = build_compare_parser()
    _args = _parser.parse_args()
    sys.exit(run_compare(_args))
