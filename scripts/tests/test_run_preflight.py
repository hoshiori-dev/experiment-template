import json

from conftest import EXP, FakeGh, Repo, finish_run, no_sleep, record_yaml, spec_text, start_run

import run_preflight
from _records import sha256_digest
from test_epic_status import issue as epic_issue


def fetch_data(repo: Repo, name="food101-subset", version="sha256:" + "ab" * 32):
    repo.write(f".local/data/{name}/VERSION", version + "\n")


def graphql(issue):
    return json.dumps({"data": {"repository": {"issue": issue}}})


def approved_gh(epic=None, parent={"number": 7}):
    return FakeGh(
        {
            "repo view": (0, "o/r\n", ""),
            "pr list": (0, json.dumps([{"number": 41, "labels": [{"name": "spec:approved"}]}]), ""),
            "issue view": (0, json.dumps({"parent": parent}), ""),
            "api graphql": (0, graphql(epic or epic_issue()), ""),
        }
    )


def test_ready_run_passes(experiment: Repo, capsys):
    start_run(experiment, "R001")
    fetch_data(experiment)
    gh = approved_gh()
    assert run_preflight.main([EXP, "R001"], gh, no_sleep) == 0
    assert "ready to start" in capsys.readouterr().out
    assert ["issue", "view", "23", "--repo", "o/r", "--json", "parent"] in gh.calls
    assert any("n=7" in call for call in gh.calls if call[:2] == ["api", "graphql"])


def test_invalid_or_missing_epic_blocks_the_run(experiment: Repo, capsys):
    start_run(experiment, "R001")
    fetch_data(experiment)
    assert run_preflight.main([EXP, "R001"], approved_gh(epic=epic_issue(state="CLOSED")), no_sleep) == 1
    assert "#7: issue is closed" in capsys.readouterr().out
    assert run_preflight.main([EXP, "R001"], approved_gh(parent=None), no_sleep) == 1
    assert "#23: has no parent issue" in capsys.readouterr().out


def test_skip_platform_does_not_confirm_approval(experiment: Repo, capsys):
    start_run(experiment, "R001")
    fetch_data(experiment)
    gh = FakeGh({})
    assert run_preflight.main([EXP, "R001", "--skip-platform"], gh, no_sleep) == 0
    assert "Epic validity are not confirmed" in capsys.readouterr().out
    assert gh.calls == []


def test_unapproved_and_unreachable(experiment: Repo, capsys):
    start_run(experiment, "R001")
    fetch_data(experiment)
    gh = approved_gh()
    gh.responses["pr list"] = [(0, "[]", "")]
    assert run_preflight.main([EXP, "R001"], gh, no_sleep) == 1
    assert "no open pull request" in capsys.readouterr().out
    gh = FakeGh({"repo view": (0, "o/r\n", ""), "pr list": (1, "", "dial tcp: i/o timeout")})
    assert run_preflight.main([EXP, "R001"], gh, no_sleep) == 2


def test_dirty_tree_wrong_branch_and_extra_commit(experiment: Repo, capsys):
    start_run(experiment, "R001")
    fetch_data(experiment)
    experiment.write("scratch.txt", "x\n")
    assert run_preflight.main([EXP, "R001", "--skip-platform"]) == 1
    assert "uncommitted changes (scratch.txt)" in capsys.readouterr().out
    experiment.commit(f"{EXP}: second commit")
    assert run_preflight.main([EXP, "R001", "--skip-platform"]) == 1
    out = capsys.readouterr().out
    assert "has 2 commits beyond" in out
    experiment.checkout(EXP)
    assert run_preflight.main([EXP, "R001", "--skip-platform"]) == 1
    assert f"check out run/{EXP}/R001" in capsys.readouterr().out


def test_record_must_be_added_by_head(experiment: Repo, capsys):
    start_run(experiment, "R001")
    experiment.checkout(EXP)
    experiment.merge(f"run/{EXP}/R001")
    experiment.branch(f"run/{EXP}/R002")
    experiment.commit(f"{EXP}: add R002", {f"experiments/{EXP}/runs/R002.yaml": record_yaml("R002")})
    experiment.commit(f"{EXP}: tweak", {f"experiments/{EXP}/runs/R002.requirements.txt": "x==1\n"})
    assert run_preflight.main([EXP, "R002", "--skip-platform"]) == 1
    out = capsys.readouterr().out
    assert "added by a commit other than HEAD" in out


def test_environment_files_and_params_must_be_committed(experiment: Repo, capsys):
    experiment.branch(f"run/{EXP}/R001")
    experiment.commit(f"{EXP}: add R001", {f"experiments/{EXP}/runs/R001.yaml": record_yaml("R001")})
    assert run_preflight.main([EXP, "R001", "--skip-platform"]) == 1
    out = capsys.readouterr().out
    assert "environment.requirements is not committed" in out
    assert "params_path is not committed" in out


def test_spec_digest_and_data_version(experiment: Repo, capsys):
    stale = sha256_digest(spec_text(limit=9))
    start_run(experiment, "R001", spec_digest=stale)
    fetch_data(experiment, version="sha256:" + "cd" * 32)
    assert run_preflight.main([EXP, "R001", "--skip-platform"]) == 1
    out = capsys.readouterr().out
    assert "spec_digest does not match" in out
    assert "holds a different version" in out


def test_missing_data_and_gpu(experiment: Repo, capsys, monkeypatch):
    start_run(experiment, "R001", resources={"accelerator": "gpu", "count": 1})
    monkeypatch.setattr(run_preflight.shutil, "which", lambda name: None)
    assert run_preflight.main([EXP, "R001", "--skip-platform"]) == 1
    out = capsys.readouterr().out
    assert "is not fetched" in out
    assert "nvidia-smi: not found" in out


def test_budget_must_fit_including_other_branches(experiment: Repo, capsys):
    start_run(experiment, "R001", budget={"reserved": 0.3})
    experiment.checkout(EXP)
    start_run(experiment, "R002", budget={"reserved": 0.2})
    fetch_data(experiment)
    assert run_preflight.main([EXP, "R002", "--skip-platform"]) == 1
    assert "budget spent 0.5 exceeds the limit 0.4" in capsys.readouterr().out


def test_budget_counts_runs_merged_after_this_branch_was_cut(experiment: Repo, capsys):
    start_run(experiment, "R002", budget={"reserved": 0.2})
    experiment.checkout(EXP)
    start_run(experiment, "R001", budget={"reserved": 0.3})
    finish_run(experiment, "R001", "completed", 0.3)
    experiment.checkout(EXP)
    experiment.merge(f"run/{EXP}/R001")
    experiment.git("branch", "-D", f"run/{EXP}/R001")
    experiment.checkout(f"run/{EXP}/R002")
    fetch_data(experiment)
    assert run_preflight.main([EXP, "R002", "--skip-platform"]) == 1
    assert "budget spent 0.5 exceeds the limit 0.4" in capsys.readouterr().out


def test_finished_record_cannot_start_again(experiment: Repo, capsys):
    start_run(experiment, "R001")
    finish_run(experiment, "R001")
    experiment.git("reset", "-q", "--soft", "HEAD~1")
    experiment.git("commit", "-q", "--amend", "--no-edit")
    fetch_data(experiment)
    assert run_preflight.main([EXP, "R001", "--skip-platform"]) == 1
    assert "already has an outcome" in capsys.readouterr().out
