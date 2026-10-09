"""Check whether an experiment's spec is approved: label ``spec:approved`` on its open PR.

Usage: spec_approval.py <exp-id> [--repo OWNER/REPO] [--json]

Runs ``gh pr list --head <exp-id> --state open`` (read-only) and looks for the label.

Exit codes: 0 approved; 1 no open pull request for the branch or the label is absent;
2 the platform could not be queried (network failures are retried first).
"""

from __future__ import annotations

import argparse
import json
import sys
import time

from _gh import GhUnreachable, Runner, add_repo_option, gh_json, resolve_repo, run_gh

APPROVAL_LABEL = "spec:approved"


def check(exp_id: str, repo: str | None, runner: Runner = run_gh, sleep=time.sleep) -> dict:
    """{"valid": bool, "pr": number | None, "reasons": [...]}; raises GhUnreachable."""
    repo = resolve_repo(repo, runner, sleep)
    prs = gh_json(
        [
            "pr",
            "list",
            "--repo",
            repo,
            "--head",
            exp_id,
            "--state",
            "open",
            "--json",
            "number,labels",
        ],
        runner,
        sleep,
    )
    if not prs:
        return {
            "valid": False,
            "pr": None,
            "reasons": [f"{exp_id}: no open pull request for this branch; open one with the spec"],
        }
    for pr in prs:
        if any(label.get("name") == APPROVAL_LABEL for label in pr.get("labels", [])):
            return {"valid": True, "pr": pr["number"], "reasons": []}
    numbers = ", ".join(f"#{pr['number']}" for pr in prs)
    return {
        "valid": False,
        "pr": prs[0]["number"],
        "reasons": [f"{exp_id}: label {APPROVAL_LABEL} is absent on {numbers}; ask the approver"],
    }


def main(argv: list[str] | None = None, runner: Runner = run_gh, sleep=time.sleep) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("exp_id", metavar="exp-id")
    add_repo_option(parser)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        result = check(args.exp_id, args.repo, runner, sleep)
    except GhUnreachable as error:
        print(f"{args.exp_id}: platform unreachable, approval unknown ({error})")
        return 2
    if args.json:
        print(json.dumps(result, indent=2))
    elif result["valid"]:
        print(f"{args.exp_id}: approved on #{result['pr']}")
    else:
        print("\n".join(result["reasons"]))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
