"""CLI sub-command: logslice label — add a derived label field to each record."""

from __future__ import annotations

import argparse
import json
import sys

from logslice.label import apply_labels, parse_label_expr
from logslice.parser import parse_line


def build_label_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs: dict = dict(
        prog="logslice label",
        description="Attach a label field derived from an existing field value.",
    )
    if parent is not None:
        parser = parent.add_parser("label", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)
    parser.add_argument(
        "expr",
        help="Mapping expression: 'src->dst:val1=label1,val2=label2[,*=default]'",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Input file (default: stdin)",
    )
    parser.add_argument(
        "--output",
        choices=["json", "logfmt"],
        default="json",
        help="Output format (default: json)",
    )
    return parser


def run_label(args: argparse.Namespace, out=None) -> None:
    if out is None:  # pragma: no cover
        out = sys.stdout

    try:
        source_field, target_field, rules, default = parse_label_expr(args.expr)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    fh = sys.stdin if args.file == "-" else open(args.file)
    try:
        for raw in fh:
            raw = raw.rstrip("\n")
            if not raw:
                continue
            record = parse_line(raw)
            if record is None:
                continue
            labeled = apply_labels([record], source_field, target_field, rules, default)
            rec = labeled[0]
            if args.output == "json":
                out.write(json.dumps(rec) + "\n")
            else:
                pairs = " ".join(
                    f'{k}="{v}"' if " " in str(v) else f"{k}={v}"
                    for k, v in rec.items()
                )
                out.write(pairs + "\n")
    finally:
        if args.file != "-":
            fh.close()


def main() -> None:  # pragma: no cover
    parser = build_label_parser()
    args = parser.parse_args()
    run_label(args)


if __name__ == "__main__":  # pragma: no cover
    main()
