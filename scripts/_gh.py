"""Read-only GitHub access through the ``gh`` CLI.

``gh_json`` runs ``gh <args>`` and parses its JSON output. A non-zero exit whose stderr
mentions the network or a timeout is retried three times with backoff; any other failure,
or three failed attempts, raises ``GhUnreachable``. Tests pass a fake ``runner`` and a
no-op ``sleep`` so nothing touches the network.
"""

from __future__ import annotations

import json
import subprocess
import time
from collections.abc import Callable

Runner = Callable[[list[str]], tuple[int, str, str]]

RETRIES = 3
NETWORK_MARKERS = (
    "network",
    "timeout",
    "timed out",
    "connection",
    "dial tcp",
    "could not resolve host",
    "no such host",
    "tls",
    "unexpected eof",
    "502",
    "503",
    "504",
)


class GhUnreachable(RuntimeError):
    """The platform could not be queried; the caller exits 2 and never assumes validity."""


def run_gh(args: list[str]) -> tuple[int, str, str]:
    """Default runner: ``gh <args>`` as a subprocess."""
    try:
        result = subprocess.run(["gh", *args], capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return 127, "", "gh: command not found; install the GitHub CLI"
    return result.returncode, result.stdout, result.stderr


def looks_like_network_error(stderr: str) -> bool:
    lowered = stderr.lower()
    return any(marker in lowered for marker in NETWORK_MARKERS)


def gh_output(
    args: list[str],
    runner: Runner = run_gh,
    sleep: Callable[[float], None] = time.sleep,
) -> str:
    """stdout of ``gh <args>``; retries network failures with 1, 2, 4 second backoff."""
    stderr = ""
    for attempt in range(RETRIES):
        code, stdout, stderr = runner(args)
        if code == 0:
            return stdout
        if not looks_like_network_error(stderr):
            break
        if attempt < RETRIES - 1:
            sleep(2**attempt)
    raise GhUnreachable(f"gh {' '.join(args)}: {stderr.strip() or f'exit {code}'}")


def gh_json(
    args: list[str],
    runner: Runner = run_gh,
    sleep: Callable[[float], None] = time.sleep,
):
    """Parsed JSON from ``gh <args>``."""
    stdout = gh_output(args, runner, sleep)
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as error:
        raise GhUnreachable(f"gh {' '.join(args)}: output is not JSON ({error})")


def default_repo(runner: Runner = run_gh, sleep=time.sleep) -> str:
    """``OWNER/REPO`` of the git remote ``origin`` as gh resolves it."""
    return gh_output(
        ["repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"],
        runner,
        sleep,
    ).strip()


def add_repo_option(parser) -> None:
    parser.add_argument(
        "--repo",
        metavar="OWNER/REPO",
        help="repository to query (default: the git remote origin)",
    )


def resolve_repo(repo: str | None, runner: Runner = run_gh, sleep=time.sleep) -> str:
    return repo or default_repo(runner, sleep)
