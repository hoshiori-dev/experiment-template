import pytest
from conftest import FakeGh, no_sleep

import _gh


def test_retries_network_errors_with_backoff():
    gh = FakeGh(
        {
            "api graphql": [
                (1, "", "error connecting to api.github.com: dial tcp: i/o timeout"),
                (1, "", 'Post "https://api.github.com/graphql": net/http: request canceled (timeout)'),
                (0, '{"ok": true}', ""),
            ]
        }
    )
    sleeps = []
    assert _gh.gh_json(["api", "graphql"], gh, sleeps.append) == {"ok": True}
    assert len(gh.calls) == 3 and sleeps == [1, 2]


def test_gives_up_after_three_network_failures():
    gh = FakeGh({"pr list": (1, "", "dial tcp: connection refused")})
    with pytest.raises(_gh.GhUnreachable):
        _gh.gh_json(["pr", "list"], gh, no_sleep)
    assert len(gh.calls) == 3


def test_other_failures_are_not_retried():
    gh = FakeGh({"pr list": (1, "", "GraphQL: Could not resolve to a Repository")})
    with pytest.raises(_gh.GhUnreachable):
        _gh.gh_json(["pr", "list"], gh, no_sleep)
    assert len(gh.calls) == 1


def test_non_json_output_is_unreachable():
    gh = FakeGh({"pr list": (0, "not json", "")})
    with pytest.raises(_gh.GhUnreachable):
        _gh.gh_json(["pr", "list"], gh, no_sleep)


def test_default_repo_comes_from_gh_repo_view():
    gh = FakeGh({"repo view": (0, "owner/name\n", "")})
    assert _gh.resolve_repo(None, gh, no_sleep) == "owner/name"
    assert _gh.resolve_repo("given/repo", gh, no_sleep) == "given/repo"
    assert gh.calls == [["repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"]]
