import json
import os
import subprocess
from pathlib import Path

import pytest
from conftest import Repo

import outbound_check

# Every pattern is assembled at runtime so this file itself passes the repository's scanners.
AWS_KEY = "AKIA" + "ABCDEFGHIJKLMNOP"
FAKE_BINARY = "/opt/fake/gitleaks"
REAL_RUN = subprocess.run


class FakeGitleaks:
    """Stands in for subprocess.run on gitleaks calls: records argv, writes ``leaks`` as the report."""

    def __init__(self, leaks=None, returncode=None):
        self.leaks = leaks or []
        self.returncode = 3 if leaks else 0 if returncode is None else returncode
        self.calls: list[list[str]] = []
        self.snapshots: list[list[str]] = []

    def __call__(self, cmd, **kwargs):
        if cmd[0] != FAKE_BINARY:
            return REAL_RUN(cmd, **kwargs)
        self.calls.append(cmd)
        if cmd[1] == "dir":
            root = Path(cmd[2])
            self.snapshots.append(sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()))
        Path(cmd[cmd.index("-r") + 1]).write_text(json.dumps(self.leaks))

        class Result:
            returncode = self.returncode
            stderr = "boom"

        return Result()


@pytest.fixture
def gitleaks(monkeypatch):
    fake = FakeGitleaks()
    monkeypatch.setattr(outbound_check, "find_gitleaks", lambda: FAKE_BINARY)
    monkeypatch.setattr(outbound_check.subprocess, "run", fake)
    return fake


def test_find_gitleaks_prefers_path_then_newest_cache_build(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(outbound_check.shutil, "which", lambda name: "/usr/bin/gitleaks")
    assert outbound_check.find_gitleaks() == "/usr/bin/gitleaks"

    monkeypatch.setattr(outbound_check.shutil, "which", lambda name: None)
    monkeypatch.setattr(outbound_check.Path, "home", lambda: tmp_path)
    assert outbound_check.find_gitleaks() is None
    old = tmp_path / ".cache/pre-commit/repoaaa/golangenv-default/bin/gitleaks"
    new = tmp_path / ".cache/pre-commit/repobbb/golangenv-default/bin/gitleaks"
    for index, binary in enumerate((old, new)):
        binary.parent.mkdir(parents=True)
        binary.write_text("#!/bin/sh\n")
        binary.chmod(0o755)
        os.utime(binary, (1_000_000 + index, 1_000_000 + index))
    assert outbound_check.find_gitleaks() == str(new)


def test_missing_gitleaks_exits_2_with_install_hint(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setattr(outbound_check, "find_gitleaks", lambda: None)
    assert outbound_check.main([str(tmp_path)]) == 2
    assert "pre-commit install --install-hooks" in capsys.readouterr().out


def test_usage_errors(tmp_path: Path, gitleaks, capsys):
    for argv in ([], ["--tree", "--git-range"], [str(tmp_path), "--tree"]):
        with pytest.raises(SystemExit) as info:
            outbound_check.main(argv)
        assert info.value.code == 2
    assert outbound_check.main([str(tmp_path / "missing")]) == 2
    assert gitleaks.calls == []


def test_paths_report_rule_and_location_only(tmp_path: Path, gitleaks, capsys):
    gitleaks.leaks = [{"RuleID": "aws-access-token", "File": "x/leak.py", "StartLine": 3, "Secret": AWS_KEY}]
    gitleaks.returncode = 3
    (tmp_path / "x").mkdir()
    assert outbound_check.main([str(tmp_path / "x")]) == 1
    out = capsys.readouterr().out
    assert "x/leak.py:3: aws-access-token" in out
    assert AWS_KEY not in out
    assert gitleaks.calls[0][:3] == [FAKE_BINARY, "dir", str(tmp_path / "x")]


def test_clean_path_passes(tmp_path: Path, gitleaks, capsys):
    assert outbound_check.main([str(tmp_path)]) == 0
    assert "no findings" in capsys.readouterr().out


def test_scanner_failure_exits_2(tmp_path: Path, gitleaks, capsys):
    gitleaks.returncode = 1
    assert outbound_check.main([str(tmp_path)]) == 2
    assert "gitleaks exited 1" in capsys.readouterr().out


def test_git_range_uses_pre_commit_refs(repo: Repo, gitleaks, monkeypatch):
    base = repo.head()
    head = repo.commit("a: clean", {"clean.txt": "fine\n"})
    monkeypatch.setenv("PRE_COMMIT_FROM_REF", base)
    monkeypatch.setenv("PRE_COMMIT_TO_REF", head)
    assert outbound_check.main(["--git-range"]) == 0
    assert gitleaks.calls[0][1:3] == ["git", f"--log-opts={base}..{head}"]


def test_git_range_new_branch_falls_back_to_whole_history(repo: Repo, gitleaks, monkeypatch):
    head = repo.commit("a: clean", {"clean.txt": "fine\n"})
    monkeypatch.setenv("PRE_COMMIT_FROM_REF", "0" * 40)
    monkeypatch.setenv("PRE_COMMIT_TO_REF", head)
    assert outbound_check.main(["--git-range"]) == 0
    assert gitleaks.calls[0][1:3] == ["git", f"--log-opts={head}"]


def test_tree_copies_tracked_and_untracked_files_only(repo: Repo, gitleaks, capsys):
    repo.commit("a: tracked", {"tracked.txt": "fine\n", "docs/.gitleaks.toml": ""})
    repo.write("untracked.txt", "fine\n")
    repo.write(".local/secret.txt", f"key = {AWS_KEY}\n")
    os.symlink("tracked.txt", repo.path / "link.txt")
    gitleaks.leaks = [{"RuleID": "aws-access-token", "File": "placeholder", "StartLine": 1}]
    gitleaks.returncode = 3
    assert outbound_check.main(["--tree"]) == 1
    root = gitleaks.calls[0][2]
    assert gitleaks.snapshots == [[".gitignore", "docs/.gitleaks.toml", "tracked.txt", "untracked.txt"]]
    gitleaks.leaks[0]["File"] = f"{root}/untracked.txt"
    assert outbound_check.format_findings(gitleaks.leaks, strip=root + "/") == ["untracked.txt:1: aws-access-token"]
    assert not Path(root).exists()
