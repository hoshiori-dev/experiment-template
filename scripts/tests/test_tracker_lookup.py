import json
import sqlite3
from pathlib import Path

import pytest
from conftest import EXP

import tracker_lookup

SCHEMA = """
CREATE TABLE metrics (id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL,
  timestamp TEXT NOT NULL, run_name TEXT NOT NULL, step INTEGER NOT NULL,
  metrics TEXT NOT NULL, log_id TEXT, space_id TEXT);
CREATE TABLE configs (id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL,
  run_name TEXT NOT NULL, config TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(run_id));
"""


def make_db(root: Path, runs: list[tuple[str, str, dict, int]]) -> Path:
    """Trackio-shaped project database; runs = (run_id, run_name, config, metric rows)."""
    root.mkdir(parents=True, exist_ok=True)
    db_path = root / f"{EXP}.db"
    db = sqlite3.connect(db_path)
    db.executescript(SCHEMA)
    for run_id, run_name, config, rows in runs:
        db.execute(
            "INSERT INTO configs (run_id, run_name, config, created_at) VALUES (?, ?, ?, ?)",
            (run_id, run_name, json.dumps(config).encode(), "2026-10-09T00:00:00"),
        )
        for step in range(rows):
            db.execute(
                "INSERT INTO metrics (run_id, timestamp, run_name, step, metrics) VALUES (?, ?, ?, ?, ?)",
                (run_id, "2026-10-09T00:00:01", run_name, step, json.dumps({"loss": 1.0 / (step + 1)}).encode()),
            )
    db.commit()
    db.close()
    return db_path


@pytest.fixture
def tracker_root(tmp_path: Path) -> Path:
    root = tmp_path / "trackio"
    make_db(
        root,
        [
            ("a" * 32, "R001", {"formal_run": f"{EXP}/R001", "source_commit": "abc123", "lr": 0.01}, 5),
            ("b" * 32, "R002", {"formal_run": f"{EXP}/R002", "source_commit": "def456"}, 0),
            ("c" * 32, "scratch", {"lr": 0.1}, 2),
        ],
    )
    return root


def test_lookup_finds_run_by_formal_run(tracker_root: Path):
    found = tracker_lookup.lookup(tracker_root, EXP, "R001")
    assert found == [{"run_id": "a" * 32, "run_name": "R001", "source_commit": "abc123", "metric_rows": 5}]
    assert tracker_lookup.lookup(tracker_root, EXP, "R003") == []


def test_cli_exit_codes(tracker_root: Path, capsys):
    assert tracker_lookup.main([EXP, "R001", "--tracker-root", str(tracker_root)]) == 0
    out = capsys.readouterr().out
    assert "run_name=R001" in out and "source_commit=abc123" in out and "metric_rows=5" in out
    assert tracker_lookup.main([EXP, "R003", "--tracker-root", str(tracker_root)]) == 1
    assert "no tracker run carries this formal_run" in capsys.readouterr().out
    assert tracker_lookup.main(["exp-999-none-here", "R001", "--tracker-root", str(tracker_root)]) == 2
    assert "tracker database not found" in capsys.readouterr().out


def test_json_output(tracker_root: Path, capsys):
    assert tracker_lookup.main([EXP, "R002", "--tracker-root", str(tracker_root), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)[0]["metric_rows"] == 0


def test_lookup_does_not_create_a_database(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        tracker_lookup.lookup(tmp_path, EXP, "R001")
    assert not (tmp_path / f"{EXP}.db").exists()
