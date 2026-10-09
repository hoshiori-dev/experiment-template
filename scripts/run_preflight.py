"""Check every start condition of a formal run that a machine can check.

Usage: run_preflight.py <exp-id> <R###> [--skip-platform] [--repo OWNER/REPO]

Conditions: clean working tree; on branch ``run/<exp-id>/<R###>`` with exactly one commit
beyond the experiment branch ``<exp-id>``; the record and every file named under its
``environment`` committed in that commit; the record valid; ``spec_digest`` equal to the
digest of ``specs/<exp-id>/spec.md`` at HEAD; spec approval valid and the parent Epic of
issue NNN valid on the platform (both skipped with ``--skip-platform``); budget fits with
this run's reservation, computed over the experiment branch tip, every run branch and HEAD;
every declared data input present under ``.local/data/<name>/VERSION`` with the declared
version; a GPU request satisfied by a working ``nvidia-smi``.

Exit codes: 0 every condition holds; 1 at least one does not (each printed); 2 the platform
could not be queried or not in a git repository.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

import yaml

import epic_status
import spec_approval
from _gh import GhUnreachable, Runner, add_repo_option, gh_json, resolve_repo, run_gh
from _git import (
    GitError,
    commit_count,
    commit_that_added,
    current_branch,
    dirty_paths,
    repo_root,
    rev_parse,
    show_file,
)
from _records import (
    budget_base,
    compute_budget,
    parse_record,
    record_path,
    run_branch,
    sha256_digest,
    spec_path,
    validate_record,
    validate_record_location,
)


def check_local(repo: Path, exp_id: str, run_id: str) -> list[str]:
    """Every condition except platform approval; returns findings."""
    f: list[str] = []
    path = record_path(exp_id, run_id)
    branch = run_branch(exp_id, run_id)

    dirty = dirty_paths(repo)
    if dirty:
        f.append(f"{repo.name}: working tree has uncommitted changes ({', '.join(dirty[:5])}); commit or stash them")

    if current_branch(repo) != branch:
        f.append(f"{current_branch(repo) or 'detached HEAD'}: check out {branch} before starting the run")
    if rev_parse(repo, exp_id) is None:
        f.append(f"{exp_id}: experiment branch does not exist; the run branch must fork from it")
    else:
        count = commit_count(repo, f"{exp_id}..HEAD")
        if count != 1:
            f.append(f"{branch}: has {count} commits beyond {exp_id}; the source commit must be the only one")

    text = show_file(repo, "HEAD", path)
    if text is None:
        f.append(f"{path}: not committed on HEAD; the record is part of the source commit")
        return f
    head = rev_parse(repo, "HEAD")
    if commit_that_added(repo, path) != head:
        f.append(f"{path}: added by a commit other than HEAD; the source commit must add the record")
    try:
        data = parse_record(text)
    except yaml.YAMLError as error:
        return f + [f"{path}: not valid YAML ({error})"]
    if data is None:
        return f + [f"{path}: must be a YAML mapping"]
    schema = validate_record(data, path) + validate_record_location(data, path, path)
    f += schema
    if schema:
        return f
    if "outcome" in data:
        f.append(f"{path}: already has an outcome; a new run needs a new record")

    for key, value in data["environment"].items():
        if show_file(repo, "HEAD", value) is None:
            f.append(f"{value}: environment.{key} is not committed on HEAD")
    if data["params_source"] in {"git", "mixed"} and show_file(repo, "HEAD", data["params_path"]) is None:
        f.append(f"{data['params_path']}: params_path is not committed on HEAD")

    spec = show_file(repo, "HEAD", spec_path(exp_id))
    if spec is None:
        f.append(f"{spec_path(exp_id)}: not committed on HEAD")
    elif sha256_digest(spec) != data["spec_digest"]:
        f.append(f"{path}: spec_digest does not match {spec_path(exp_id)} at HEAD; recompute it")

    budget = compute_budget(repo, exp_id, base=budget_base(repo, exp_id), extra_refs=("HEAD",))
    f += budget.findings
    if budget.limit is not None and "budget" not in data:
        f.append(f"{path}: budget.reserved is missing but the spec sets a limit")
    if not budget.fits:
        f.append(f"{exp_id}: budget spent {budget.spent:g} exceeds the limit {budget.limit:g} {budget.unit}")

    for entry in data["data"]:
        marker = repo / ".local" / "data" / entry["name"] / "VERSION"
        if not marker.is_file():
            f.append(f"{marker.relative_to(repo).as_posix()}: data input {entry['name']} is not fetched")
        elif marker.read_text(encoding="utf-8").strip() != str(entry["version"]).strip():
            f.append(f"{marker.relative_to(repo).as_posix()}: holds a different version than the record declares")

    if data["resources"]["accelerator"] == "gpu":
        if shutil.which("nvidia-smi") is None:
            f.append("nvidia-smi: not found; the run requests a GPU")
        elif subprocess.run(["nvidia-smi"], capture_output=True, check=False).returncode != 0:
            f.append("nvidia-smi: failed; the run requests a GPU")
    return f


def issue_number(exp_id: str) -> int:
    """The experiment issue number encoded in ``exp-NNN-<slug>``."""
    return int(exp_id.split("-")[1])


def check_platform(exp_id: str, repo: str | None, runner: Runner, sleep) -> list[str]:
    """Spec approval and parent Epic validity; raises GhUnreachable."""
    repo = resolve_repo(repo, runner, sleep)
    findings = spec_approval.check(exp_id, repo, runner, sleep)["reasons"]
    number = issue_number(exp_id)
    parent = gh_json(["issue", "view", str(number), "--repo", repo, "--json", "parent"], runner, sleep).get("parent")
    if not parent:
        return findings + [f"#{number}: has no parent issue; an experiment issue is a sub-issue of its Epic"]
    return findings + epic_status.check(parent["number"], repo, runner, sleep)["reasons"]


def main(argv: list[str] | None = None, runner: Runner = run_gh, sleep=time.sleep) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("exp_id", metavar="exp-id")
    parser.add_argument("run_id", metavar="R###")
    parser.add_argument("--skip-platform", action="store_true", help="do not query the platform")
    add_repo_option(parser)
    args = parser.parse_args(argv)

    try:
        repo = repo_root()
        findings = check_local(repo, args.exp_id, args.run_id)
    except GitError as error:
        print(f"run_preflight: {error}")
        return 2

    unreachable = False
    if args.skip_platform:
        print(f"{args.exp_id}: platform check skipped; spec approval and Epic validity are not confirmed")
    else:
        try:
            findings += check_platform(args.exp_id, args.repo, runner, sleep)
        except GhUnreachable as error:
            findings.append(f"{args.exp_id}: platform unreachable, approval and Epic validity unknown ({error})")
            unreachable = True

    for finding in findings:
        print(finding)
    if unreachable:
        return 2
    if findings:
        return 1
    print(f"{args.exp_id}/{args.run_id}: ready to start")
    return 0


if __name__ == "__main__":
    sys.exit(main())
