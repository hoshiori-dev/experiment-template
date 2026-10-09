"""Print the source commit of a formal run: the commit that added its record file.

Usage: source_commit.py <exp-id> <R###> [--verify-tracker] [--tracker-root DIR]

Looks for ``experiments/<exp-id>/runs/<R###>.yaml`` in the history of HEAD, then on the
run branch ``run/<exp-id>/<R###>`` when HEAD does not have it. With ``--verify-tracker`` the
hash is compared with the ``source_commit`` the tracker stored for ``<exp-id>/<R###>``.

Exit codes: 0 found (and matching the tracker when asked); 1 record never committed or the
tracker disagrees; 2 not in a git repository or tracker storage unreadable.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

from _git import GitError, commit_that_added, repo_root, rev_parse
from _records import record_path, run_branch
from tracker_lookup import DEFAULT_ROOT, lookup


def find_source_commit(repo: Path, exp_id: str, run_id: str) -> str | None:
    path = record_path(exp_id, run_id)
    found = commit_that_added(repo, path)
    if found is None and rev_parse(repo, run_branch(exp_id, run_id)):
        found = commit_that_added(repo, path, run_branch(exp_id, run_id))
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("exp_id", metavar="exp-id")
    parser.add_argument("run_id", metavar="R###")
    parser.add_argument(
        "--verify-tracker",
        action="store_true",
        help="compare with the source_commit stored in local tracker storage",
    )
    parser.add_argument("--tracker-root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args(argv)

    try:
        repo = repo_root()
    except GitError as error:
        print(f"source_commit: {error}")
        return 2
    path = record_path(args.exp_id, args.run_id)
    commit = find_source_commit(repo, args.exp_id, args.run_id)
    if commit is None:
        print(f"{path}: no commit added this record; commit it on {run_branch(args.exp_id, args.run_id)}")
        return 1
    print(commit)
    if not args.verify_tracker:
        return 0

    try:
        runs = lookup(args.tracker_root, args.exp_id, args.run_id)
    except FileNotFoundError as error:
        print(f"{Path(str(error)).as_posix()}: tracker database not found")
        return 2
    except sqlite3.Error as error:
        print(f"{args.tracker_root}: cannot read tracker storage ({error})")
        return 2
    formal_run = f"{args.exp_id}/{args.run_id}"
    if not runs:
        print(f"{formal_run}: no tracker run carries this formal_run")
        return 1
    if len(runs) > 1:
        print(f"{formal_run}: {len(runs)} tracker runs carry this formal_run; expected one")
        return 1
    stored = runs[0]["source_commit"]
    if stored != commit:
        print(f"{formal_run}: tracker source_commit {stored} differs from git {commit}")
        return 1
    print(f"{formal_run}: tracker source_commit matches")
    return 0


if __name__ == "__main__":
    sys.exit(main())
