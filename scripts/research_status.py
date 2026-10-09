"""Report the state of every experiment from git and files alone; no platform access.

Usage: research_status.py

For each experiment found under ``specs/`` or ``experiments/``: the README status line, runs
with their outcomes, budget spent and limit, unmerged run branches. Then the ``synthesis/*``
branches and whether ``specs/`` and ``experiments/`` list the same experiments.

Exit codes: 0 report printed (the report itself may name problems); 2 not in a git repository.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from _git import GitError, branches, repo_root
from _records import EXP_ID_RE, budget_base, compute_budget, unmerged_run_branches

STATUS_VALUES = ("in progress", "answered", "answer is negative", "inconclusive")
STATUS_LINE_RE = re.compile(r"^\**status\**\s*:\s*\**(.+?)\**\s*$", re.I)


def experiment_ids(repo: Path, folder: str) -> set[str]:
    base = repo / folder
    if not base.is_dir():
        return set()
    return {p.name for p in base.iterdir() if p.is_dir() and EXP_ID_RE.match(p.name)}


def readme_status(repo: Path, exp_id: str) -> str:
    readme = repo / "experiments" / exp_id / "README.md"
    if not readme.is_file():
        return "README.md missing"
    for line in readme.read_text(encoding="utf-8").splitlines():
        match = STATUS_LINE_RE.match(line.strip())
        if match:
            value = match.group(1).strip()
            if value.lower() in STATUS_VALUES:
                return value
            return f"{value} (not one of: {', '.join(STATUS_VALUES)})"
    return "no 'Status:' line in README.md"


def report_lines(repo: Path) -> list[str]:
    specs = experiment_ids(repo, "specs")
    experiments = experiment_ids(repo, "experiments")
    lines = []
    for exp_id in sorted(specs | experiments):
        base = budget_base(repo, exp_id)
        budget = compute_budget(repo, exp_id, base=base)
        runs = ", ".join(f"{run.run_id} {run.outcome or 'no outcome'}" for run in budget.runs)
        unmerged = unmerged_run_branches(repo, exp_id, base)
        lines.append(exp_id)
        lines.append(f"  status: {readme_status(repo, exp_id)}")
        lines.append(f"  runs: {runs or 'none'}")
        if budget.limit is None:
            lines.append(f"  budget: {budget.spent:g} spent, no limit")
        else:
            lines.append(f"  budget: {budget.spent:g} of {budget.limit:g} {budget.unit}")
        lines.append(f"  unmerged run branches: {', '.join(unmerged) or 'none'}")
        for finding in budget.findings:
            lines.append(f"  problem: {finding}")
    if not specs | experiments:
        lines.append("no experiments found under specs/ or experiments/")
    synthesis = branches(repo, "synthesis/")
    lines.append(f"synthesis branches: {', '.join(synthesis) or 'none'}")
    if specs == experiments:
        lines.append("specs/ and experiments/ agree")
    else:
        for exp_id in sorted(specs - experiments):
            lines.append(f"{exp_id}: in specs/ only; experiments/{exp_id}/README.md is missing")
        for exp_id in sorted(experiments - specs):
            lines.append(f"{exp_id}: in experiments/ only; specs/{exp_id}/spec.md is missing")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.parse_args(argv)
    try:
        lines = report_lines(repo_root())
    except GitError as error:
        print(f"research_status: {error}")
        return 2
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
