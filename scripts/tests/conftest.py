"""Shared fixtures: temporary git repositories shaped like the template, and a fake gh runner."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from _records import sha256_digest  # noqa: E402

EXP = "exp-023-normalization-instability"
GIT_IDENTITY = ["-c", "user.name=Tester", "-c", "user.email=1+tester@users.noreply.github.com"]


def spec_text(limit: float | None = 0.4, unit: str = "gpu-hours") -> str:
    front = {"experiment": EXP, "issue": 23, "holdout": "test split never read before R001"}
    if limit is not None:
        front["budget"] = {"unit": unit, "limit": limit}
    return "---\n" + yaml.safe_dump(front, sort_keys=False) + "---\n\n# Spec\n\nWhich adaptation is better?\n"


def record_dict(run_id: str = "R001", spec_digest: str | None = None, **overrides) -> dict:
    """A valid run record without execution fields; ``overrides`` replace top-level keys."""
    data = {
        "id": run_id,
        "experiment": EXP,
        "decision": "Whether fine-tuning beats a linear probe.",
        "command": "uv run python train.py --config configs/r001.yaml",
        "params_source": "git",
        "params_path": f"experiments/{EXP}/configs/{run_id.lower()}.yaml",
        "data": [
            {
                "name": "food101-subset",
                "source": "https://huggingface.co/datasets/food101",
                "version": "sha256:" + "ab" * 32,
                "path": ".local/data/food101-subset",
            }
        ],
        "resources": {"accelerator": "cpu", "count": 1},
        "max_duration": "PT2H",
        "environment": {"requirements": f"experiments/{EXP}/runs/{run_id}.requirements.txt"},
        "budget": {"reserved": 0.2},
        "spec_digest": spec_digest or sha256_digest(spec_text()),
        "tracker": {"project": EXP, "run": run_id},
    }
    data.update(overrides)
    for key in [key for key, value in data.items() if value is None]:
        del data[key]
    return data


def record_yaml(run_id: str = "R001", spec_digest: str | None = None, **overrides) -> str:
    return yaml.safe_dump(record_dict(run_id, spec_digest, **overrides), sort_keys=False)


class Repo:
    """A temporary git repository with helpers that keep test bodies short."""

    def __init__(self, path: Path):
        self.path = path

    def git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", *GIT_IDENTITY, *args], cwd=self.path, capture_output=True, text=True, check=True
        )
        return result.stdout.strip()

    def write(self, relative: str, content: str) -> Path:
        file = self.path / relative
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding="utf-8")
        return file

    def commit(self, message: str, files: dict[str, str] | None = None) -> str:
        for relative, content in (files or {}).items():
            self.write(relative, content)
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", message)
        return self.git("rev-parse", "HEAD")

    def branch(self, name: str, start: str | None = None) -> None:
        self.git("checkout", "-q", "-b", name, *([start] if start else []))

    def checkout(self, name: str) -> None:
        self.git("checkout", "-q", name)

    def merge(self, name: str) -> str:
        self.git("merge", "-q", "--no-ff", "--no-edit", name)
        return self.git("rev-parse", "HEAD")

    def head(self) -> str:
        return self.git("rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path: Path, monkeypatch) -> Repo:
    """Empty repository on branch main with one commit (.gitignore for .local/); cwd set to it."""
    path = tmp_path / "repo"
    path.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=path, check=True)
    repo = Repo(path)
    repo.commit("init: start repository", {".gitignore": ".local/\n"})
    monkeypatch.chdir(path)
    return repo


@pytest.fixture
def experiment(repo: Repo) -> Repo:
    """Spec on main, experiment branch checked out, README with a status line."""
    repo.commit(
        f"{EXP}: add spec",
        {
            f"specs/{EXP}/spec.md": spec_text(),
            f"experiments/{EXP}/README.md": "# Normalization\n\nStatus: in progress\n",
        },
    )
    repo.branch(EXP)
    return repo


def start_run(repo: Repo, run_id: str = "R001", **overrides) -> str:
    """Create run/<EXP>/<run_id> from the current branch with one source commit; return its hash."""
    repo.branch(f"run/{EXP}/{run_id}")
    files = {
        f"experiments/{EXP}/runs/{run_id}.yaml": record_yaml(run_id, **overrides),
        f"experiments/{EXP}/runs/{run_id}.requirements.txt": "numpy==2.0.0 --hash=sha256:0000\n",
        f"experiments/{EXP}/configs/{run_id.lower()}.yaml": "lr: 0.01\n",
    }
    return repo.commit(f"{EXP}: add {run_id} record", files)


def finish_run(repo: Repo, run_id: str, outcome: str = "completed", actual_usage: float = 0.1) -> str:
    """Append execution fields to the record on the current (run) branch and commit."""
    file = repo.path / f"experiments/{EXP}/runs/{run_id}.yaml"
    data = yaml.safe_load(file.read_text(encoding="utf-8"))
    data.update(
        {
            "outcome": outcome,
            "execution_ref": "docker:sha256:feed",
            "failure_reason": "" if outcome == "completed" else "out of time",
            "actual_usage": actual_usage,
            "interruptions": 0,
        }
    )
    file.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return repo.commit(f"{EXP}: record {run_id} {outcome}")


class FakeGh:
    """Runner for _gh: answers by the first two words of the gh command, records every call."""

    def __init__(self, responses: dict[str, tuple[int, str, str] | list[tuple[int, str, str]]]):
        self.responses = {key: list(value) if isinstance(value, list) else [value] for key, value in responses.items()}
        self.calls: list[list[str]] = []

    def __call__(self, args: list[str]) -> tuple[int, str, str]:
        self.calls.append(args)
        key = " ".join(args[:2])
        queue = self.responses.get(key)
        if not queue:
            return 1, "", f"fake gh: no response for {key}"
        return queue.pop(0) if len(queue) > 1 else queue[0]


def no_sleep(_seconds: float) -> None:
    pass
