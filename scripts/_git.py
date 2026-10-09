"""Git access for the harness scripts: thin subprocess wrappers, no porcelain parsing beyond lines.

Every function takes the repository path as ``repo`` and runs ``git`` there. ``GitError``
is raised when git itself fails for a reason other than "the object does not exist".
"""

from __future__ import annotations

import subprocess
from pathlib import Path


class GitError(RuntimeError):
    """git exited non-zero; the message carries git's stderr."""


def git(args: list[str], repo: Path | None = None, check: bool = True) -> str:
    """Run ``git <args>`` in ``repo`` and return stdout. With ``check`` a failure raises GitError."""
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=False)
    if check and result.returncode != 0:
        raise GitError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout


def repo_root(start: Path | None = None) -> Path:
    """Top-level directory of the repository containing ``start`` (default: the cwd)."""
    return Path(git(["rev-parse", "--show-toplevel"], start).strip())


def current_branch(repo: Path) -> str | None:
    """Name of the checked-out branch, or None when HEAD is detached."""
    name = git(["rev-parse", "--abbrev-ref", "HEAD"], repo).strip()
    return None if name == "HEAD" else name


def branches(repo: Path, prefix: str = "") -> list[str]:
    """Local branch names starting with ``prefix``, sorted."""
    out = git(["for-each-ref", "--format=%(refname:short)", f"refs/heads/{prefix}"], repo)
    return sorted(line for line in out.splitlines() if line)


def rev_parse(repo: Path, ref: str) -> str | None:
    """Full commit hash of ``ref``, or None when it does not resolve."""
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def show_file(repo: Path, ref: str, path: str) -> str | None:
    """Content of ``path`` at ``ref``, or None when the file is absent there."""
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


def commit_that_added(repo: Path, path: str, ref: str = "HEAD") -> str | None:
    """Hash of the most recent commit reachable from ``ref`` that added ``path``."""
    out = git(["log", "--diff-filter=A", "--format=%H", ref, "--", path], repo)
    lines = out.split()
    return lines[0] if lines else None


def dirty_paths(repo: Path) -> list[str]:
    """Paths with uncommitted changes, untracked files included (``git status --porcelain``)."""
    out = git(["status", "--porcelain", "--untracked-files=all"], repo)
    return [line[3:] for line in out.splitlines() if line]


def is_ancestor(repo: Path, commit: str, ref: str) -> bool:
    """True when ``commit`` is reachable from ``ref``."""
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, ref],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def merge_base(repo: Path, a: str, b: str) -> str | None:
    """Best common ancestor of ``a`` and ``b``, or None when they share no history."""
    result = subprocess.run(
        ["git", "merge-base", a, b],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def commit_count(repo: Path, rev_range: str) -> int:
    """Number of commits selected by ``rev_range`` (for example ``main..HEAD``)."""
    return int(git(["rev-list", "--count", rev_range], repo).strip())


def staged_paths(repo: Path) -> list[str]:
    """Paths staged for the next commit."""
    out = git(["diff", "--cached", "--name-only"], repo)
    return [line for line in out.splitlines() if line]


def changed_paths(repo: Path, rev_range: str) -> list[str]:
    """Paths touched by the commits in ``rev_range``."""
    out = git(["diff", "--name-only", rev_range], repo)
    return [line for line in out.splitlines() if line]
