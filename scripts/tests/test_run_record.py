import pytest
from conftest import EXP, record_dict, record_yaml

import run_record
from _records import validate_record, validate_record_location


def findings(**overrides) -> str:
    return "\n".join(validate_record(record_dict(**overrides), "rec"))


def test_valid_record_has_no_findings():
    assert validate_record(record_dict(), "rec") == []


def test_valid_finished_record():
    data = record_dict(outcome="failed", failure_reason="OOM", actual_usage=0.05, interruptions=1)
    assert validate_record(data, "rec") == []


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"id": "run1"}, "id must look like R001"),
        ({"experiment": "exp-23-x"}, "experiment must look like"),
        ({"decision": None}, "decision is missing"),
        ({"params_source": "yaml"}, "params_source must be one of"),
        ({"params_path": None}, "params_path is missing"),
        ({"params_path": "/home/" + "someone/config.yaml"}, "params_path must be a relative repo path"),
        ({"max_duration": "2h"}, "max_duration must be an ISO-8601 duration"),
        ({"resources": {"accelerator": "tpu", "count": 1}}, "accelerator must be cpu or gpu"),
        ({"resources": {"accelerator": "gpu", "count": 0}}, "count must be a positive integer"),
        ({"environment": {}}, "environment must map"),
        ({"environment": {"dockerfile": "../outside/Dockerfile"}}, "environment.dockerfile must be a relative"),
        ({"budget": {"reserved": "lots"}}, "budget.reserved must be a non-negative number"),
        ({"spec_digest": "abc"}, "spec_digest must be sha256:"),
        ({"tracker": {"project": EXP}}, "tracker.run is missing"),
        ({"outcome": "done", "actual_usage": 1}, "outcome must be completed, failed or aborted"),
        ({"outcome": "completed"}, "actual_usage must be a non-negative number once an outcome is set"),
        ({"outcome": "aborted", "actual_usage": 0}, "failure_reason must say why the run aborted"),
        ({"actual_usage": 0.1}, "actual_usage is set but outcome is missing"),
        ({"interruptions": -1}, "interruptions must be a non-negative integer"),
        ({"metrics": {"loss": 0.1}}, "metrics is not a record field"),
        ({"command": "python /home/" + "alice/train.py"}, "rec.command: names a home directory"),
    ],
)
def test_each_rule_names_the_field(overrides, expected):
    assert expected in findings(**overrides)


@pytest.mark.parametrize("version", ["latest", "main", "2026-10-09", "20261009", "release/1", "", None])
def test_mutable_versions_are_rejected(version):
    data = record_dict()
    data["data"][0]["version"] = version
    assert "data[0].version must be an immutable content identifier" in "\n".join(validate_record(data, "rec"))


def test_data_entries_must_be_complete():
    data = record_dict(data=[{"name": "x"}])
    text = "\n".join(validate_record(data, "rec"))
    assert "data[0].source is missing" in text
    assert "data[0].path must be a relative repo path" in text


def test_location_must_match_id_and_experiment():
    data = record_dict()
    path = f"experiments/{EXP}/runs/R002.yaml"
    assert validate_record_location(data, path, path) == [f"{path}: id must be R002 to match the file name"]
    assert validate_record_location(data, "somewhere/R001.yaml", "x") == []


def test_cli_exit_codes(tmp_path, capsys):
    good = tmp_path / "R001.yaml"
    good.write_text(record_yaml())
    assert run_record.main(["validate", str(good)]) == 0
    bad = tmp_path / "R002.yaml"
    bad.write_text(record_yaml(max_duration="forever"))
    assert run_record.main(["validate", str(good), str(bad)]) == 1
    assert "R002.yaml: max_duration" in capsys.readouterr().out
    assert run_record.main(["validate", str(tmp_path / "none.yaml")]) == 2
    broken = tmp_path / "R003.yaml"
    broken.write_text("id: [unclosed\n")
    assert run_record.main(["validate", str(broken)]) == 1
