from conftest import EXP, Repo

import check_branch_scope as cbs


def test_experiment_branch_allows_only_its_directories():
    paths = [f"specs/{EXP}/spec.md", f"experiments/{EXP}/README.md", "scripts/budget.py", "specs/exp-024-other-one/x"]
    findings = cbs.findings_for(EXP, paths)
    assert [line.split(":")[0] for line in findings] == ["scripts/budget.py", "specs/exp-024-other-one/x"]


def test_run_branch_uses_the_same_scope():
    assert cbs.findings_for(f"run/{EXP}/R007", [f"experiments/{EXP}/runs/R007.yaml"]) == []
    assert len(cbs.findings_for(f"run/{EXP}/R007", ["README.md"])) == 1


def test_other_branches_pass_and_misnamed_ones_do_not():
    assert cbs.findings_for("main", ["scripts/budget.py"]) == []
    assert cbs.findings_for("synthesis/5", ["docs/x.md"]) == []
    assert cbs.findings_for("feature/anything", ["anything"]) == []
    assert cbs.findings_for(None, ["anything"]) == []
    assert "branch name must be" in cbs.findings_for("exp-23-bad", ["x"])[0]
    assert "branch name must be" in cbs.findings_for("run/exp-023-a/R001", ["x"])[0]


def test_cli_reads_staged_paths(repo: Repo, capsys):
    repo.branch(EXP)
    repo.write(f"specs/{EXP}/spec.md", "---\n---\n")
    repo.write("justfile", "x\n")
    repo.git("add", "-A")
    assert cbs.main([]) == 1
    assert capsys.readouterr().out.startswith("justfile: outside")
    repo.git("reset", "-q", "justfile")
    assert cbs.main([]) == 0


def test_outside_git(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert cbs.main([]) == 2
