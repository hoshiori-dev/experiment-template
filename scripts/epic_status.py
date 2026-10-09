"""Decide whether an Epic issue is valid, from four conditions read through ``gh``.

Usage: epic_status.py <issue-number> [--repo OWNER/REPO] [--json]

Valid means all of: the issue is open; it carries the label ``epic:approved``; that label
was added after creation (an event within 5 s of createdAt by the issue author counts as
"at creation"); the body was not edited after the label was added (lastEditedAt is null
or earlier than the labeled event). One GraphQL query, read-only.

Exit codes: 0 valid; 1 invalid (reasons printed); 2 the platform could not be queried.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timedelta

from _gh import GhUnreachable, Runner, add_repo_option, gh_json, resolve_repo, run_gh

APPROVAL_LABEL = "epic:approved"
AT_CREATION_WINDOW = timedelta(seconds=5)

QUERY = """
query($owner: String!, $name: String!, $n: Int!) {
  repository(owner: $owner, name: $name) {
    issue(number: $n) {
      number state createdAt lastEditedAt
      author { login }
      labels(first: 50) { nodes { name } }
      timelineItems(first: 100, itemTypes: [LABELED_EVENT, UNLABELED_EVENT]) {
        nodes {
          __typename
          ... on LabeledEvent { createdAt actor { login } label { name } }
          ... on UnlabeledEvent { createdAt actor { login } label { name } }
        }
      }
    }
  }
}
"""


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def evaluate(issue: dict) -> list[str]:
    """Reasons the Epic is invalid; empty when all four conditions hold."""
    number = issue.get("number")
    reasons = []
    if issue.get("state") != "OPEN":
        reasons.append(f"#{number}: issue is {str(issue.get('state')).lower()}, not open")
    labels = {node["name"] for node in issue.get("labels", {}).get("nodes", [])}
    if APPROVAL_LABEL not in labels:
        reasons.append(f"#{number}: label {APPROVAL_LABEL} is absent; a maintainer adds it")
        return reasons

    events = [
        node
        for node in issue.get("timelineItems", {}).get("nodes", [])
        if node.get("label", {}).get("name") == APPROVAL_LABEL
    ]
    labeled = [node for node in events if node["__typename"] == "LabeledEvent"]
    if not labeled:
        reasons.append(f"#{number}: no labeled event for {APPROVAL_LABEL} in the timeline")
        return reasons
    last = max(labeled, key=lambda node: node["createdAt"])
    labeled_at = parse_time(last["createdAt"])
    created_at = parse_time(issue["createdAt"])
    actor = (last.get("actor") or {}).get("login")
    author = (issue.get("author") or {}).get("login")
    if labeled_at - created_at <= AT_CREATION_WINDOW and actor == author:
        reasons.append(
            f"#{number}: {APPROVAL_LABEL} was set at creation by the author; "
            "a maintainer must add it after reading the Epic"
        )
    edited = issue.get("lastEditedAt")
    if edited and parse_time(edited) >= labeled_at:
        reasons.append(
            f"#{number}: body edited at {edited}, after the label was added at "
            f"{last['createdAt']}; a maintainer must re-add {APPROVAL_LABEL}"
        )
    return reasons


def check(number: int, repo: str | None, runner: Runner = run_gh, sleep=time.sleep) -> dict:
    """{"valid": bool, "reasons": [...]}; raises GhUnreachable."""
    repo = resolve_repo(repo, runner, sleep)
    owner, name = repo.split("/", 1)
    data = gh_json(
        [
            "api",
            "graphql",
            "-F",
            f"owner={owner}",
            "-F",
            f"name={name}",
            "-F",
            f"n={number}",
            "-f",
            f"query={QUERY}",
        ],
        runner,
        sleep,
    )
    issue = ((data.get("data") or {}).get("repository") or {}).get("issue")
    if not issue:
        raise GhUnreachable(f"#{number}: not an issue in {repo}")
    reasons = evaluate(issue)
    return {"valid": not reasons, "number": number, "reasons": reasons}


def main(argv: list[str] | None = None, runner: Runner = run_gh, sleep=time.sleep) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("number", type=int, metavar="issue-number")
    add_repo_option(parser)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        result = check(args.number, args.repo, runner, sleep)
    except GhUnreachable as error:
        print(f"#{args.number}: platform unreachable, Epic validity unknown ({error})")
        return 2
    if args.json:
        print(json.dumps(result, indent=2))
    elif result["valid"]:
        print(f"#{args.number}: Epic is valid")
    else:
        print("\n".join(result["reasons"]))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
