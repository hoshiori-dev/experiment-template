from conftest import EXP, Repo, finish_run, spec_text, start_run

import research_status


def test_report_covers_runs_budget_branches_and_agreement(experiment: Repo, capsys):
    start_run(experiment, "R001")
    finish_run(experiment, "R001", "completed", 0.11)
    experiment.checkout(EXP)
    experiment.merge(f"run/{EXP}/R001")
    start_run(experiment, "R002")
    experiment.checkout(EXP)
    experiment.branch("synthesis/5", "main")
    experiment.commit("synthesis: start", {"specs/exp-031-second-thing/spec.md": spec_text(limit=None)})
    experiment.checkout(EXP)

    assert research_status.main([]) == 0
    out = capsys.readouterr().out
    assert "status: in progress" in out
    assert "runs: R001 completed, R002 no outcome" in out
    assert "budget: 0.31 of 0.4 gpu-hours" in out
    assert f"unmerged run branches: run/{EXP}/R002" in out
    assert "synthesis branches: synthesis/5" in out
    assert "specs/ and experiments/ agree" in out


def test_disagreement_and_status_line_problems(experiment: Repo, capsys):
    experiment.commit(
        f"{EXP}: add another",
        {
            "specs/exp-031-second-thing/spec.md": spec_text(limit=None),
            "experiments/exp-032-third-thing/README.md": "# Third\n\nStatus: maybe\n",
            f"experiments/{EXP}/README.md": "# No status here\n",
        },
    )
    assert research_status.main([]) == 0
    out = capsys.readouterr().out
    assert "exp-031-second-thing: in specs/ only" in out
    assert "exp-032-third-thing: in experiments/ only" in out
    assert "maybe (not one of: in progress, answered, answer is negative, inconclusive)" in out
    assert "no 'Status:' line" in out
    assert "exp-032-third-thing\n  status" in out


def test_empty_repository(repo: Repo, capsys):
    assert research_status.main([]) == 0
    assert "no experiments found" in capsys.readouterr().out


def test_outside_git(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert research_status.main([]) == 2
