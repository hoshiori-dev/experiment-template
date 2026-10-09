"""Check an experiment's budget against its run records, unmerged run branches included.

Usage: budget.py <exp-id> [--reserve X] [--json]

spent = sum of actual_usage over records with an outcome + sum of budget.reserved over
records without one. Records on unmerged ``run/<exp-id>/R###`` branches count. The spec's
``budget.limit`` is the bound; a spec without a budget block is unlimited. ``--reserve X``
asks whether a new run reserving X would still fit.

Exit codes: 0 fits; 1 over the limit or records that cannot be accounted for; 2 not in a
git repository.
"""

from __future__ import annotations

import argparse
import json
import sys

from _git import GitError, repo_root
from _records import BudgetReport, compute_budget


def describe(report: BudgetReport) -> list[str]:
    lines = []
    for run in report.runs:
        if run.data is None:
            continue
        if run.outcome is None:
            lines.append(f"  {run.run_id} reserved {run.reserved} ({run.origin})")
        else:
            lines.append(f"  {run.run_id} {run.outcome} {run.actual_usage} ({run.origin})")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("exp_id", metavar="exp-id")
    parser.add_argument("--reserve", type=float, default=0.0, metavar="X", help="amount a new run would reserve")
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    args = parser.parse_args(argv)

    try:
        repo = repo_root()
    except GitError as error:
        print(f"budget: {error}")
        return 2
    report = compute_budget(repo, args.exp_id, args.reserve)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        if report.limit is None:
            print(f"{args.exp_id}: no budget block in spec; unlimited; spent {report.spent:g}")
        else:
            print(
                f"{args.exp_id}: spent {report.spent:g} of {report.limit:g} {report.unit}"
                + (f", reserving {report.reserve:g}" if report.reserve else "")
            )
        print("\n".join(describe(report)))
        for finding in report.findings:
            print(finding)
        if not report.fits:
            print(
                f"{args.exp_id}: spent {report.spent + report.reserve:g} exceeds the limit "
                f"{report.limit:g}; finish or abort a run, lower the reservation, "
                "or ask the approver for more budget"
            )
    return 0 if report.fits and not report.findings else 1


if __name__ == "__main__":
    sys.exit(main())
