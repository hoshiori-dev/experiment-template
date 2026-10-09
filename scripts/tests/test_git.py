from conftest import Repo

import _git


def test_branch_queries(repo: Repo):
    assert _git.current_branch(repo.path) == "main"
    repo.branch("run/exp-001-a-b/R001")
    repo.commit("a: one")
    repo.checkout("main")
    repo.branch("run/exp-001-a-b/R002")
    assert _git.branches(repo.path, "run/exp-001-a-b/") == ["run/exp-001-a-b/R001", "run/exp-001-a-b/R002"]
    assert _git.branches(repo.path, "synthesis/") == []
    repo.git("checkout", "-q", "--detach")
    assert _git.current_branch(repo.path) is None


def test_show_file_and_commit_that_added(repo: Repo):
    first = repo.commit("a: add file", {"a.txt": "one\n"})
    repo.commit("a: change file", {"a.txt": "two\n"})
    assert _git.show_file(repo.path, first, "a.txt") == "one\n"
    assert _git.show_file(repo.path, "HEAD", "a.txt") == "two\n"
    assert _git.show_file(repo.path, "HEAD", "missing.txt") is None
    assert _git.commit_that_added(repo.path, "a.txt") == first
    assert _git.commit_that_added(repo.path, "missing.txt") is None


def test_dirty_paths_include_untracked(repo: Repo):
    assert _git.dirty_paths(repo.path) == []
    repo.write("new.txt", "x\n")
    assert _git.dirty_paths(repo.path) == ["new.txt"]


def test_ancestry_and_counts(repo: Repo):
    base = repo.head()
    repo.branch("feature/x")
    tip = repo.commit("x: one")
    repo.commit("x: two")
    assert _git.is_ancestor(repo.path, base, "feature/x")
    assert not _git.is_ancestor(repo.path, tip, "main")
    assert _git.merge_base(repo.path, "main", "feature/x") == base
    assert _git.commit_count(repo.path, "main..feature/x") == 2
    assert _git.rev_parse(repo.path, "nope") is None


def test_staged_and_changed_paths(repo: Repo):
    repo.write("staged.txt", "s\n")
    repo.git("add", "staged.txt")
    assert _git.staged_paths(repo.path) == ["staged.txt"]
    before = repo.head()
    repo.commit("a: commit staged")
    assert _git.changed_paths(repo.path, f"{before}..HEAD") == ["staged.txt"]
