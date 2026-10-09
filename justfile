# Task entry points for the harness. Scripts live in scripts/ and run with the root
# environment (uv sync creates .venv). Recipes take positional arguments ("$@").

set positional-arguments

# Spec Kit's bash helpers need a python with PyYAML; the root .venv has it after uv sync.

export SPECKIT_PYTHON_EXECUTABLE := justfile_directory() / ".venv/bin/python"

# Same ruff version as the ruff-pre-commit rev in .pre-commit-config.yaml.

ruff := "uvx ruff@0.11.9"
specify := "uvx --from git+https://github.com/github/spec-kit.git@v1.1.2 specify"

# Format check, lint, tests and run-record validation (what CI runs).
check: lint test validate-records
    deno fmt --check
    just --fmt --check --unstable
    {{ ruff }} format --check scripts

# Format everything in place.
fmt:
    deno fmt
    just --fmt --unstable
    {{ ruff }} format scripts
    {{ ruff }} check --fix scripts

# Static checks without changing files.
lint:
    {{ ruff }} check scripts

# Tests of the harness scripts.
test:
    uv run pytest scripts/tests

# Validate every run record in the working tree.
validate-records:
    #!/usr/bin/env bash
    set -euo pipefail
    records=$(find experiments -path 'experiments/*/runs/R[0-9][0-9][0-9].yaml' 2>/dev/null | sort || true)
    if [ -z "$records" ]; then
        echo "no run records under experiments/*/runs/"
        exit 0
    fi
    uv run python scripts/run_record.py validate $records

# Budget spent and remaining for an experiment: just budget <exp-id> [--reserve X] [--json]
budget exp *args:
    uv run python scripts/budget.py "$@"

# Start conditions of a formal run: just preflight <exp-id> <R###> [--skip-platform]
preflight exp run *args:
    uv run python scripts/run_preflight.py "$@"

# Epic validity on the platform (read-only): just epic-status <issue-number> [--json]
epic-status number *args:
    uv run python scripts/epic_status.py "$@"

# Spec approval label on the experiment's PR (read-only): just spec-approval <exp-id>
spec-approval exp *args:
    uv run python scripts/spec_approval.py "$@"

# Research status from git and record files (read-only).
status *args:
    uv run python scripts/research_status.py "$@"

# Outbound check of files or directories before they leave the machine: just outbound <path>...
outbound +paths:
    uv run python scripts/outbound_check.py "$@"

# Secret and PII scan of the working tree as git sees it (tracked and untracked files, ignored ones skipped).
scan:
    uv run python scripts/outbound_check.py --tree

# Source commit of a formal run: just source-commit <exp-id> <R###> [--verify-tracker] [--tracker-root DIR]
source-commit exp run *args:
    uv run python scripts/source_commit.py "$@"

# Tracker runs tagged with a formal run: just tracker <exp-id> <R###> [--tracker-root DIR] [--json]
tracker exp run *args:
    uv run python scripts/tracker_lookup.py "$@"

# Reinstall the research preset and extension from speckit/; needed only after editing speckit/ (the committed .specify/ copies work on a fresh checkout).
speckit-install:
    echo y | {{ specify }} preset remove research || true
    echo y | {{ specify }} extension remove research || true
    {{ specify }} preset add --dev speckit/preset
    {{ specify }} extension add --dev speckit/extension

# Run the skills CLI with Deno.
skills *args:
    deno run -A --no-lock npm:skills "$@"
