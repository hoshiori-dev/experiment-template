"""Pre-commit hook: on experiment and run branches, staged paths stay inside the experiment.

Usage: check_branch_scope.py

On branch ``exp-NNN-<slug>`` or ``run/exp-NNN-<slug>/R###`` every staged path must be under
``specs/<id>/`` or ``experiments/<id>/``. A branch starting with ``exp-`` or ``run/`` that
does not follow the naming rule is a finding. Every other branch passes.

Exit codes: 0 in scope; 1 a staged path is outside the experiment (each one printed);
2 not in a git repository.
"""

from __future__ import annotations

import argparse
import re
import sys

from _git import GitError, current_branch, repo_root, staged_paths
from _records import EXP_ID_RE

RUN_BRANCH_RE = re.compile(r"^run/([^/]+)/R\d{3}$")


def experiment_of(branch: str) -> str | None:
    """Experiment id a branch belongs to, or None when the branch is not scoped."""
    match = RUN_BRANCH_RE.match(branch)
    candidate = match.group(1) if match else branch
    return candidate if EXP_ID_RE.match(candidate) else None


def findings_for(branch: str | None, paths: list[str]) -> list[str]:
    if branch is None:
        return []
    exp_id = experiment_of(branch)
    if exp_id is None:
        if branch.startswith(("exp-", "run/")):
            return [f"{branch}: branch name must be exp-NNN-<slug> (2-4 lowercase words) or run/exp-NNN-<slug>/R###"]
        return []
    allowed = (f"specs/{exp_id}/", f"experiments/{exp_id}/")
    return [
        f"{path}: outside {' and '.join(allowed)}; commit shared changes on a separate branch"
        for path in paths
        if not path.startswith(allowed)
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.parse_args(argv)
    try:
        repo = repo_root()
        findings = findings_for(current_branch(repo), staged_paths(repo))
    except GitError as error:
        print(f"check_branch_scope: {error}")
        return 2
    for finding in findings:
        print(finding)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
