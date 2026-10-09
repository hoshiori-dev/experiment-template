"""Scan content that is about to leave the machine; report rule and location, never the match.

Usage: outbound_check.py <path>... [--config .gitleaks.toml]
       outbound_check.py --git-range [--config .gitleaks.toml]
       outbound_check.py --tree [--config .gitleaks.toml]

With paths: runs ``gitleaks dir`` over each path with the repository config. With
``--git-range`` (pre-push hook): reads ``PRE_COMMIT_FROM_REF``/``PRE_COMMIT_TO_REF`` and runs
``gitleaks git --log-opts=<from>..<to>``; an all-zero or empty FROM (new branch) falls back to
``git merge-base origin/main HEAD``, and to the whole local history when that fails. With
``--tree``: scans the working tree as git sees it (tracked and untracked files, ignored ones
skipped) in one ``gitleaks dir`` call over a temporary copy. gitleaks is taken from PATH,
else from the pre-commit cache (``~/.cache/pre-commit/repo*/golangenv-default/bin/gitleaks``,
newest first), which ``pre-commit install --install-hooks`` fills.

Exit codes: 0 nothing found; 1 findings (``file:line: rule-id``); 2 usage error, gitleaks
missing or scanner failure.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from _git import GitError, merge_base, repo_root

ZERO_REF = "0" * 40
CACHE_GLOB = "repo*/golangenv-default/bin/gitleaks"
NOT_FOUND = "gitleaks not found: run 'pre-commit install --install-hooks' or put gitleaks on PATH"


def find_gitleaks() -> str | None:
    """Path of the gitleaks binary: PATH first, then the newest build in the pre-commit cache."""
    on_path = shutil.which("gitleaks")
    if on_path:
        return on_path
    cached = [p for p in (Path.home() / ".cache" / "pre-commit").glob(CACHE_GLOB) if os.access(p, os.X_OK)]
    if not cached:
        return None
    return str(max(cached, key=lambda p: p.stat().st_mtime))


def gitleaks_findings(binary: str, args: list[str]) -> list[dict]:
    """Run gitleaks with a JSON report and return the raw leak entries; raises on failure."""
    with tempfile.TemporaryDirectory() as tmp:
        report = Path(tmp) / "report.json"
        result = subprocess.run(
            [binary, *args, "--no-banner", "--exit-code", "3", "-f", "json", "-r", str(report)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode not in (0, 3):
            raise RuntimeError(f"gitleaks exited {result.returncode}: {result.stderr.strip()}")
        return json.loads(report.read_text(encoding="utf-8") or "[]")


def format_findings(leaks: list[dict], strip: str = "") -> list[str]:
    lines = []
    for leak in leaks:
        file = str(leak.get("File"))
        if strip and file.startswith(strip):
            file = file[len(strip) :]
        lines.append(f"{file}:{leak.get('StartLine')}: {leak.get('RuleID')}")
    return lines


def resolve_range(repo: Path) -> tuple[str | None, str]:
    """(from, to) for the pre-push scan; from is None when the whole history must be scanned."""
    from_ref = os.environ.get("PRE_COMMIT_FROM_REF", "")
    to_ref = os.environ.get("PRE_COMMIT_TO_REF") or "HEAD"
    if from_ref and from_ref != ZERO_REF:
        return from_ref, to_ref
    return merge_base(repo, "origin/main", "HEAD"), to_ref


def scan_range(binary: str, repo: Path, config: Path) -> list[str]:
    from_ref, to_ref = resolve_range(repo)
    log_opts = f"{from_ref}..{to_ref}" if from_ref else to_ref
    leaks = gitleaks_findings(binary, ["git", f"--log-opts={log_opts}", "--config", str(config), str(repo)])
    return format_findings(leaks)


def tree_paths(repo: Path) -> list[str]:
    """Tracked and untracked files as git lists them, ignored files left out."""
    out = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [p for p in out.split("\0") if p]


def scan_tree(binary: str, repo: Path, config: Path) -> list[str]:
    """One ``gitleaks dir`` call over a temporary copy of the listed files (symlinks skipped)."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "tree"
        for relative in tree_paths(repo):
            source = repo / relative
            if source.is_symlink() or not source.is_file():
                continue
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        root.mkdir(exist_ok=True)
        leaks = gitleaks_findings(binary, ["dir", str(root), "--config", str(config.resolve())])
    return format_findings(leaks, strip=str(root) + "/")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--git-range", action="store_true", help="scan outgoing commits")
    parser.add_argument("--tree", action="store_true", help="scan the working tree as git sees it")
    parser.add_argument("--config", type=Path, default=Path(".gitleaks.toml"))
    args = parser.parse_args(argv)
    if bool(args.paths) + args.git_range + args.tree != 1:
        parser.error("give paths to scan, or --git-range alone, or --tree alone")

    binary = find_gitleaks()
    if binary is None:
        print(f"outbound_check: {NOT_FOUND}")
        return 2
    try:
        if args.git_range:
            findings = scan_range(binary, repo_root(), args.config)
        elif args.tree:
            findings = scan_tree(binary, repo_root(), args.config)
        else:
            findings = []
            for path in args.paths:
                if not path.exists():
                    print(f"{path.as_posix()}: path not found")
                    return 2
                findings += format_findings(gitleaks_findings(binary, ["dir", str(path), "--config", str(args.config)]))
    except (GitError, RuntimeError, subprocess.CalledProcessError, json.JSONDecodeError) as error:
        print(f"outbound_check: {error}")
        return 2

    for finding in findings:
        print(finding)
    if findings:
        print(f"outbound_check: {len(findings)} finding(s); rewrite the content and scan again")
        return 1
    print("outbound_check: no findings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
