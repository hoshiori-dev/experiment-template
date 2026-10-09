import json

from conftest import EXP, FakeGh, no_sleep

import spec_approval


def prs(*label_sets):
    return json.dumps(
        [{"number": 40 + i, "labels": [{"name": n} for n in names]} for i, names in enumerate(label_sets)]
    )


def test_approved_when_open_pr_carries_label(capsys):
    gh = FakeGh({"repo view": (0, "o/r\n", ""), "pr list": (0, prs(["spec:approved"]), "")})
    assert spec_approval.main([EXP], gh, no_sleep) == 0
    assert "approved on #40" in capsys.readouterr().out
    assert gh.calls[-1][:7] == ["pr", "list", "--repo", "o/r", "--head", EXP, "--state"]


def test_missing_label_or_pr_is_invalid(capsys):
    gh = FakeGh({"pr list": (0, prs(["experiment"]), "")})
    assert spec_approval.main([EXP, "--repo", "o/r"], gh, no_sleep) == 1
    assert "spec:approved is absent on #40" in capsys.readouterr().out
    gh = FakeGh({"pr list": (0, "[]", "")})
    assert spec_approval.main([EXP, "--repo", "o/r", "--json"], gh, no_sleep) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["valid"] is False and "no open pull request" in result["reasons"][0]


def test_unreachable_platform_exits_2(capsys):
    gh = FakeGh({"pr list": (1, "", "dial tcp: i/o timeout")})
    assert spec_approval.main([EXP, "--repo", "o/r"], gh, no_sleep) == 2
    assert "approval unknown" in capsys.readouterr().out
    assert len(gh.calls) == 3
