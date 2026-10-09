# Harness scripts

Checks that keep the research loop honest. Each script is a plain Python 3.12 file (standard library plus PyYAML) with a
`main()`, run as `uv run python scripts/<name>.py ...` or through the `justfile` recipes. Findings print as
`<file-or-object>: <what to fix>`. Exit codes are shared: `0` ok, `1` violation, `2` the question could not be answered
(usage error, not a git repository, platform unreachable). Helpers (`_git.py`, `_records.py`, `_gh.py`) are imported
from the scripts' own directory, which Python puts on `sys.path` when a script runs as a file; the tests do the same in
`tests/conftest.py`. Tests: `uv run pytest scripts/tests -q`; they build throwaway git repositories and use a fake `gh`
runner, so nothing touches the network.

## run_record.py

`run_record.py validate <record>...` checks run records against the schema in the harness knowledge: required definition
fields, enumerations (`params_source`, `accelerator`, `outcome`), ISO-8601 `max_duration`, immutable data versions
(never `latest`, a date or a branch name), relative repo paths only, no home directories, drives, users or hosts in any
string, execution fields consistent with the outcome, and `id`/`experiment` matching the file's location. Exit `2` when
a file is missing. The harness runs it as a pre-commit hook on staged records and in CI over every record
(`just validate-records`).

## budget.py

`budget.py <exp-id> [--reserve X] [--json]` computes spent = actual usage of finished runs + reservations of unfinished
runs, reading records at the budget base (the experiment branch tip when that branch exists, else HEAD) and on every
`run/<exp-id>/R###` branch the base does not contain, and compares it with `budget.limit` in the spec's front matter. A
spec without a budget block is unlimited. `--reserve X` asks whether a new run reserving `X` still fits. Exit `1` when
the limit is exceeded or a record cannot be accounted for (a missing reservation, an outcome without usage). The agent
runs it before writing a run record and `run_preflight.py` runs it again before a run starts (`just budget <exp>`).

## source_commit.py

`source_commit.py <exp-id> <R###> [--verify-tracker] [--tracker-root DIR]` prints the commit that added the record file,
looking at HEAD first and at the run branch when HEAD does not have it. `--verify-tracker` compares that hash with the
`source_commit` the tracker stored for `<exp-id>/<R###>` (via `tracker_lookup.py`); exit `1` when the record was never
committed or the tracker disagrees, `2` when tracker storage is missing. The agent runs it with `--verify-tracker` for
every finished run before an experiment is handed back.

## run_preflight.py

`run_preflight.py <exp-id> <R###> [--skip-platform] [--repo OWNER/REPO]` checks every start condition a machine can
check: clean working tree; on branch `run/<exp-id>/<R###>` with exactly one commit beyond the experiment branch, and
that commit added the record; every file named under the record's `environment` and its `params_path` committed; record
valid; `spec_digest` equal to the digest of `specs/<exp-id>/spec.md` at HEAD; no outcome yet; spec approval valid on the
platform and the parent Epic of issue NNN valid (`epic_status.check`, the parent read with
`gh issue view NNN --json parent`); budget fits, computed over the budget base of `budget.py` plus HEAD's own record;
every declared data input present under `.local/data/<name>/VERSION` with the declared version; a GPU request satisfied
by a working `nvidia-smi`. `--skip-platform` leaves approval and Epic validity unconfirmed and says so. Exit `2` when
the platform cannot be reached. The agent runs it immediately before launching a formal run
(`just preflight <exp> <run>`).

## epic_status.py

`epic_status.py <issue-number> [--repo OWNER/REPO] [--json]` decides whether an Epic is valid with one read-only GraphQL
query: open; labelled `epic:approved`; the label added after creation (an event within 5 s of `createdAt` by the issue
author counts as "at creation"); body not edited after that label event. Network failures are retried three times with
backoff; exit `2` when the platform stays unreachable, and validity is never assumed. The agent runs it before creating
an experiment and before every formal run (`just epic-status <n>`).

## spec_approval.py

`spec_approval.py <exp-id> [--repo OWNER/REPO] [--json]` finds the open pull request whose head branch is `<exp-id>` and
checks for the label `spec:approved`. Exit `1` when there is no such pull request or the label is absent, `2` when the
platform is unreachable. `run_preflight.py` calls it; the agent runs it on its own after a spec changes
(`just spec-approval <exp>`).

## research_status.py

`research_status.py` reports from git and files alone: for each experiment found under `specs/` or `experiments/`, the
README `Status:` line, the runs with their outcomes, budget spent and limit, unmerged run branches, then the
`synthesis/*` branches and whether `specs/` and `experiments/` list the same experiments. The report names problems
instead of failing; exit `2` only outside a git repository. Used at the start of a session and at the rendezvous
(`just
status`).

## outbound_check.py

`outbound_check.py <path>... [--config .gitleaks.toml]` scans files or directories with `gitleaks dir` and the
repository config; `outbound_check.py --git-range` scans the commits about to be pushed
(`PRE_COMMIT_FROM_REF..PRE_COMMIT_TO_REF`, falling back to `merge-base origin/main
HEAD` or the whole history for a new
branch) with `gitleaks git`; `outbound_check.py --tree` scans the working tree as git sees it (tracked and untracked
files, ignored ones skipped) with one `gitleaks dir` call over a temporary copy. gitleaks is taken from PATH, else from
the pre-commit cache (`~/.cache/pre-commit/repo*/golangenv-default/bin/gitleaks`, newest build first), which
`pre-commit install --install-hooks` fills; with neither the script exits `2` and says so. Findings are printed as
`file:line: rule-id`, never the matched text. The pre-push hook runs the `--git-range` form, `just scan` the `--tree`
form; the agent runs the path form on drafts under `.local/drafts/` and on result files before they enter the repository
(`just outbound <paths>`).

## check_commit_message.py

`check_commit_message.py <msg-file>` is the commit-msg hook. It rejects `Co-Authored-By` trailers naming an agent
(claude, codex, opencode, copilot, gemini, gpt, anthropic, openai, bot, agent), "Generated with", "Generated by" and the
robot emoji; requires a title of at most 50 ASCII characters shaped `<scope>: <summary>` with a lowercase summary and no
trailing period, a blank second line and body lines of at most 72 characters (a line without spaces, such as a URL, may
be longer); allows human co-authors only with `users.noreply.github.com` or `noreply.gitlab.com` addresses; and requires
the author address (`GIT_AUTHOR_EMAIL`, else `git var GIT_AUTHOR_IDENT`) to be a platform noreply address while the
constant `REQUIRE_NOREPLY_AUTHOR` at the top of the script is `True` (owners who allow other addresses flip it in a
preparation-phase PR). Merge commits and `fixup!`/`squash!` titles skip the title rules. Comment lines and anything
after the scissors line are ignored. Exit `2` when the message file cannot be read.

## check_branch_scope.py

`check_branch_scope.py` is a pre-commit hook. On branch `exp-NNN-<slug>` or `run/exp-NNN-<slug>/R###` every staged path
must be under `specs/<id>/` or `experiments/<id>/`; each path outside is printed. A branch starting with `exp-` or
`run/` that does not follow the naming rule is a finding. Every other branch passes.

## tracker_lookup.py

`tracker_lookup.py <exp-id> <R###> [--tracker-root DIR] [--json]` reads `<tracker-root>/<exp-id>.db` (default
`.local/trackio`) with sqlite3 and prints, for every tracker run whose config carries `formal_run: "<exp-id>/<R###>"`,
its `run_id`, `run_name`, `source_commit` and number of metric rows. Exit `1` when no run carries that tag, `2` when the
database is missing or unreadable. The database is opened read-only, so a lookup never creates one. Used by
`source_commit.py --verify-tracker` and by the agent when writing the README's evidence section.
