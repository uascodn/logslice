"""CLI helpers for template-based formatting in logslice."""
import argparse
import sys
from typing import List, Optional

from logslice.parser import parse_line
from logslice.template import parse_template_expr, apply_template


def build_template_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-template",
        description="Render log records using a template string.",
    )
    p.add_argument("file", nargs="?", default="-", help="Input log file (default: stdin)")
    p.add_argument(
        "-t", "--template",
        required=True,
        help="Template string, e.g. '{level}: {msg}'",
    )
    p.add_argument(
        "--dest",
        default="_line",
        help="Destination field name for rendered output (default: _line)",
    )
    p.add_argument(
        "--print-only",
        action="store_true",
        help="Print only the rendered field value, not the full record",
    )
    return p


def run_template(argv: Optional[List[str]] = None) -> None:
    parser = build_template_parser()
    args = parser.parse_args(argv)

    try:
        template = parse_template_expr(args.template)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.file == "-":
        lines = sys.stdin
    else:
        lines = open(args.file)

    try:
        records = (parse_line(line) for line in lines if line.strip())
        for rec in apply_template(records, template, dest_field=args.dest):
            if args.print_only:
                print(rec.get(args.dest, ""))
            else:
                import json
                print(json.dumps(rec))
    finally:
        if args.file != "-":
            lines.close()


if __name__ == "__main__":
    run_template()
