import json

from conftest import EXP, Repo, finish_run, record_yaml, spec_text, start_run

import budget
from _records import compute_budget


def test_spent_counts_finished_usage_and_open_reservations(experiment: Repo):
    start_run(experiment, "R001")
    finish_run(experiment, "R001", "completed", 0.11)
    experiment.checkout(EXP)
    experiment.merge(f"run/{EXP}/R001")
    start_run(experiment, "R002", budget={"reserved": 0.15})
    experiment.checkout(EXP)

    report = compute_budget(experiment.path, EXP)
    assert report.limit == 0.4
    assert report.spent == 0.11 + 0.15
    assert [(run.run_id, run.origin) for run in report.runs] == [("R001", EXP), ("R002", f"run/{EXP}/R002")]
    assert report.fits and report.findings == []


def test_branch_copy_of_a_record_wins_over_the_tree_copy(experiment: Repo):
    start_run(experiment, "R001")
    experiment.checkout(EXP)
    experiment.merge(f"run/{EXP}/R001")  # record without outcome is now on the experiment branch too
    experiment.checkout(f"run/{EXP}/R001")
    finish_run(experiment, "R001", "failed", 0.05)
    experiment.checkout(EXP)
    report = compute_budget(experiment.path, EXP)
    assert report.spent == 0.05
    assert report.runs[0].origin == f"run/{EXP}/R001"


def test_base_is_the_experiment_branch_tip_not_head(experiment: Repo):
    start_run(experiment, "R002", budget={"reserved": 0.2})  # cut before R001 lands on the experiment branch
    experiment.checkout(EXP)
    start_run(experiment, "R001", budget={"reserved": 0.3})
    finish_run(experiment, "R001", "completed", 0.3)
    experiment.checkout(EXP)
    experiment.merge(f"run/{EXP}/R001")
    experiment.git("branch", "-D", f"run/{EXP}/R001")
    experiment.checkout(f"run/{EXP}/R002")  # HEAD's tree has no R001

    report = compute_budget(experiment.path, EXP)
    assert [(run.run_id, run.origin) for run in report.runs] == [("R001", EXP), ("R002", f"run/{EXP}/R002")]
    assert report.spent == 0.3 + 0.2 and not report.fits
    assert compute_budget(experiment.path, EXP, base="HEAD").spent == 0.2


def test_head_is_the_base_without_an_experiment_branch(experiment: Repo):
    start_run(experiment, "R001")
    experiment.checkout(EXP)
    experiment.merge(f"run/{EXP}/R001")
    experiment.git("branch", "-m", EXP, "elsewhere")
    report = compute_budget(experiment.path, EXP)
    assert [(run.run_id, run.origin) for run in report.runs] == [("R001", "HEAD")]


def test_over_limit_and_reserve(experiment: Repo, capsys):
    start_run(experiment, "R001", budget={"reserved": 0.3})
    experiment.checkout(EXP)
    assert budget.main([EXP]) == 0
    assert budget.main([EXP, "--reserve", "0.1"]) == 0
    assert budget.main([EXP, "--reserve", "0.2"]) == 1
    assert "exceeds the limit 0.4" in capsys.readouterr().out


def test_unlimited_spec_always_fits(experiment: Repo, capsys):
    experiment.commit("spec: drop budget", {f"specs/{EXP}/spec.md": spec_text(limit=None)})
    start_run(experiment, "R001", budget=None)
    experiment.checkout(EXP)
    assert budget.main([EXP]) == 0
    assert "unlimited" in capsys.readouterr().out


def test_missing_reservation_is_a_finding_when_spec_has_limit(experiment: Repo, capsys):
    start_run(experiment, "R001", budget=None)
    experiment.checkout(EXP)
    assert budget.main([EXP]) == 1
    assert "budget.reserved is missing" in capsys.readouterr().out


def test_json_output(experiment: Repo, capsys):
    start_run(experiment, "R001")
    assert budget.main([EXP, "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["spent"] == 0.2 and data["limit"] == 0.4 and data["fits"] is True
    assert data["runs"][0]["id"] == "R001"


def test_missing_spec_is_reported(experiment: Repo, capsys):
    experiment.write(f"experiments/{EXP}/runs/R001.yaml", record_yaml())
    assert budget.main(["exp-999-no-such-thing"]) == 1
    assert "spec is missing" in capsys.readouterr().out


def test_outside_git_repository(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert budget.main([EXP]) == 2
