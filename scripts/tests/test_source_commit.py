from conftest import EXP, Repo, finish_run, start_run
from test_tracker_lookup import make_db

import source_commit


def test_prints_commit_that_added_the_record(experiment: Repo, capsys):
    source = start_run(experiment, "R001")
    finish_run(experiment, "R001")
    assert source_commit.main([EXP, "R001"]) == 0
    assert capsys.readouterr().out.strip() == source


def test_falls_back_to_the_run_branch(experiment: Repo, capsys):
    source = start_run(experiment, "R001")
    experiment.checkout(EXP)
    assert source_commit.main([EXP, "R001"]) == 0
    assert capsys.readouterr().out.strip() == source
    assert source_commit.main([EXP, "R002"]) == 1
    assert "no commit added this record" in capsys.readouterr().out


def test_verify_tracker(experiment: Repo, tmp_path, capsys):
    source = start_run(experiment, "R001")
    start_run(experiment, "R002")
    root = tmp_path / "trackio"
    make_db(
        root,
        [
            ("a" * 32, "R001", {"formal_run": f"{EXP}/R001", "source_commit": source}, 3),
            ("b" * 32, "R002", {"formal_run": f"{EXP}/R002", "source_commit": "0" * 40}, 3),
        ],
    )
    assert source_commit.main([EXP, "R001", "--verify-tracker", "--tracker-root", str(root)]) == 0
    assert "matches" in capsys.readouterr().out
    assert source_commit.main([EXP, "R002", "--verify-tracker", "--tracker-root", str(root)]) == 1
    assert "differs from git" in capsys.readouterr().out
    assert source_commit.main([EXP, "R001", "--verify-tracker", "--tracker-root", str(tmp_path / "none")]) == 2


def test_verify_tracker_requires_exactly_one_tracker_run(experiment: Repo, tmp_path, capsys):
    source = start_run(experiment, "R001")
    root = tmp_path / "trackio"
    make_db(
        root,
        [
            ("a" * 32, "R001", {"formal_run": f"{EXP}/R001", "source_commit": source}, 1),
            ("b" * 32, "R001", {"formal_run": f"{EXP}/R001", "source_commit": source}, 1),
        ],
    )
    assert source_commit.main([EXP, "R001", "--verify-tracker", "--tracker-root", str(root)]) == 1
    assert "2 tracker runs" in capsys.readouterr().out
