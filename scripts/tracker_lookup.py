"""Find a formal run in local Trackio storage and print what it recorded.

Usage: tracker_lookup.py <exp-id> <R###> [--tracker-root DIR] [--json]

Reads ``<tracker-root>/<exp-id>.db`` (default ``.local/trackio``) with sqlite3 and selects the
rows of the ``configs`` table whose config carries ``formal_run: "<exp-id>/<R###>"``. For
each row it prints run_id, run_name, source_commit and the number of metric rows.

Exit codes: 0 found; 1 no run with that formal_run; 2 database missing or unreadable.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

DEFAULT_ROOT = Path(".local/trackio")


def lookup(root: Path, exp_id: str, run_id: str) -> list[dict]:
    """Tracker runs tagged ``<exp-id>/<run_id>``; raises FileNotFoundError or sqlite3.Error."""
    db_path = root / f"{exp_id}.db"
    if not db_path.is_file():
        raise FileNotFoundError(db_path)
    db = sqlite3.connect(f"{db_path.resolve().as_uri()}?mode=ro", uri=True)
    try:
        rows = db.execute(
            "SELECT run_id, run_name, config FROM configs WHERE json_extract(config, '$.formal_run') = ?",
            (f"{exp_id}/{run_id}",),
        ).fetchall()
        found = []
        for tracker_run_id, run_name, config in rows:
            (metric_rows,) = db.execute("SELECT COUNT(*) FROM metrics WHERE run_id = ?", (tracker_run_id,)).fetchone()
            found.append(
                {
                    "run_id": tracker_run_id,
                    "run_name": run_name,
                    "source_commit": json.loads(config).get("source_commit"),
                    "metric_rows": metric_rows,
                }
            )
        return found
    finally:
        db.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("exp_id", metavar="exp-id")
    parser.add_argument("run_id", metavar="R###")
    parser.add_argument("--tracker-root", type=Path, default=DEFAULT_ROOT, help="tracker storage")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        found = lookup(args.tracker_root, args.exp_id, args.run_id)
    except FileNotFoundError as error:
        print(f"{Path(str(error)).as_posix()}: tracker database not found under {args.tracker_root}")
        return 2
    except sqlite3.Error as error:
        print(f"{args.tracker_root / (args.exp_id + '.db')}: cannot read tracker storage ({error})")
        return 2

    if args.json:
        print(json.dumps(found, indent=2))
    elif found:
        for run in found:
            print(
                f"run_id={run['run_id']} run_name={run['run_name']} "
                f"source_commit={run['source_commit']} metric_rows={run['metric_rows']}"
            )
    if not found:
        print(
            f"{args.exp_id}/{args.run_id}: no tracker run carries this formal_run; "
            "the run must call the tracker with config formal_run and source_commit"
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
