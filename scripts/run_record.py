"""Validate run records against the run record schema.

Usage: run_record.py validate <record>...

Checks every field of ``experiments/<id>/runs/R###.yaml``: required definition fields,
enumerations, ISO-8601 duration, immutable data versions, relative repo paths only, no
machine-specific strings, execution fields consistent with the outcome, and that id and
experiment match the file's location.

Exit codes: 0 all records valid; 1 at least one finding; 2 usage error or unreadable file.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from _records import parse_record, validate_record, validate_record_location


def validate_file(path: Path) -> list[str]:
    label = path.as_posix()
    try:
        data = parse_record(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        return [f"{label}: not valid YAML ({error})"]
    if data is None:
        return [f"{label}: must be a YAML mapping"]
    return validate_record(data, label) + validate_record_location(data, label, label)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[1])
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate", help="validate one or more records")
    validate.add_argument("records", nargs="+", type=Path)
    args = parser.parse_args(argv)

    findings: list[str] = []
    for record in args.records:
        if not record.is_file():
            print(f"{record.as_posix()}: file not found")
            return 2
        findings += validate_file(record)
    for finding in findings:
        print(finding)
    if findings:
        return 1
    print(f"{len(args.records)} record(s) valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
