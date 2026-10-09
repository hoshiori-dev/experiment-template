import json

from conftest import FakeGh, no_sleep

import epic_status


def issue(
    state="OPEN",
    labels=("epic", "epic:approved"),
    created="2026-10-01T10:00:00Z",
    labeled="2026-10-02T09:00:00Z",
    actor="maintainer",
    author="drafter",
    last_edited=None,
    events=None,
):
    if events is None:
        events = [
            {
                "__typename": "LabeledEvent",
                "createdAt": labeled,
                "actor": {"login": actor},
                "label": {"name": "epic:approved"},
            }
        ]
    return {
        "number": 7,
        "state": state,
        "createdAt": created,
        "lastEditedAt": last_edited,
        "author": {"login": author},
        "labels": {"nodes": [{"name": name} for name in labels]},
        "timelineItems": {"nodes": events},
    }


def test_valid_epic():
    assert epic_status.evaluate(issue()) == []


def test_closed_issue():
    assert "not open" in epic_status.evaluate(issue(state="CLOSED"))[0]


def test_missing_label():
    reasons = epic_status.evaluate(issue(labels=("epic",)))
    assert len(reasons) == 1 and "epic:approved is absent" in reasons[0]


def test_label_set_at_creation_by_author_is_invalid():
    reasons = epic_status.evaluate(issue(labeled="2026-10-01T10:00:02Z", actor="drafter"))
    assert "set at creation by the author" in reasons[0]
    # same timing by someone else counts as a real approval
    assert epic_status.evaluate(issue(labeled="2026-10-01T10:00:02Z", actor="maintainer")) == []


def test_body_edited_after_labeling_is_invalid():
    reasons = epic_status.evaluate(issue(last_edited="2026-10-03T00:00:00Z"))
    assert "body edited" in reasons[0]
    assert epic_status.evaluate(issue(last_edited="2026-10-01T12:00:00Z")) == []


def test_latest_labeled_event_counts_after_unlabel_and_relabel():
    events = [
        {
            "__typename": "LabeledEvent",
            "createdAt": "2026-10-01T10:00:01Z",
            "actor": {"login": "drafter"},
            "label": {"name": "epic:approved"},
        },
        {
            "__typename": "UnlabeledEvent",
            "createdAt": "2026-10-01T11:00:00Z",
            "actor": {"login": "maintainer"},
            "label": {"name": "epic:approved"},
        },
        {
            "__typename": "LabeledEvent",
            "createdAt": "2026-10-02T11:00:00Z",
            "actor": {"login": "maintainer"},
            "label": {"name": "epic:approved"},
        },
    ]
    assert epic_status.evaluate(issue(events=events)) == []


def graphql_response(data):
    return json.dumps({"data": {"repository": {"issue": data}}})


def test_cli_valid_and_invalid(capsys):
    gh = FakeGh({"repo view": (0, "o/r\n", ""), "api graphql": (0, graphql_response(issue()), "")})
    assert epic_status.main(["7"], gh, no_sleep) == 0
    assert "Epic is valid" in capsys.readouterr().out
    assert "-F" in gh.calls[-1] and "n=7" in gh.calls[-1]
    gh = FakeGh({"api graphql": (0, graphql_response(issue(state="CLOSED")), "")})
    assert epic_status.main(["7", "--repo", "o/r", "--json"], gh, no_sleep) == 1
    assert json.loads(capsys.readouterr().out)["valid"] is False


def test_cli_unreachable(capsys):
    gh = FakeGh({"api graphql": (1, "", "error connecting to api.github.com: timeout")})
    assert epic_status.main(["7", "--repo", "o/r"], gh, no_sleep) == 2
    assert "validity unknown" in capsys.readouterr().out
    gh = FakeGh({"api graphql": (0, json.dumps({"data": {"repository": {"issue": None}}}), "")})
    assert epic_status.main(["7", "--repo", "o/r"], gh, no_sleep) == 2
