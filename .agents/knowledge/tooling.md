# Tooling

Read this when a command, hook, config file or platform setting is the thing at hand: running a check, a check failing,
editing harness configuration, or setting up the platform. Source of truth for how the pieces fit; each tool's own files
and `--help` are authoritative for details.

## Layers

| Layer                 | What                                               | Can                                   | Cannot                                                                            |
| --------------------- | -------------------------------------------------- | ------------------------------------- | --------------------------------------------------------------------------------- |
| written rules         | `AGENTS.md`, knowledge, skills                     | explain what and why                  | prevent anything                                                                  |
| local checks          | hooks, record validation, offline tests            | stop mechanical errors before leaving | judge meaning                                                                     |
| framework permissions | command allow and deny lists per agent framework   | catch slips                           | more than prefix matching; not a boundary                                         |
| platform              | branch protection, code-owner review, token scopes | the boundary                          | be configured by the agent; tell a solo owner from the agent on the owner's token |
| agent read-through    | `outbound-review` skill                            | add meaning to the scanner            | be cheap or free of false positives                                               |
| CI                    | the local checks again on the platform             | backstop                              | prevent a leak: content is already public                                         |

## Spec Kit

Spec Kit supplies the skeletons for `spec.md`, `plan.md`, `tasks.md` and registers commands as skills; the meanings are
the project's own. Sources live in `speckit/`; installed copies in `.specify/presets/research/`,
`.specify/extensions/research/` and `.claude/skills/speckit-*/`. The Claude Code integration is the only one installed:
Codex reaches the same skills through symlinks `.agents/skills/speckit-<name>` -> `../../.claude/skills/speckit-<name>`,
and OpenCode reads `.claude/skills/` natively; there is no `.opencode/` directory. Upstream commands the project has no
use for (`analyze`, `checklist`, `clarify`, `converge`, `taskstoissues`) are replaced by stubs through the preset.
`just speckit-install` runs `specify preset add --dev speckit/preset` and
`specify extension add --dev speckit/extension` with spec-kit pinned at tag `v1.1.2` in the `justfile`; it is needed
only after editing `speckit/`, since the committed copies work on a fresh checkout. `deno fmt` excludes the Spec
Kit-managed copies (`deno.json`). The charter is `.specify/memory/constitution.md` (five principles).

| Command                        | Replaces / adds | Does                                                                |
| ------------------------------ | --------------- | ------------------------------------------------------------------- |
| `speckit.specify`              | core (preset)   | write a research spec for one Experiment                            |
| `speckit.plan`                 | core (preset)   | write or rewrite the advisory plan                                  |
| `speckit.tasks`                | core (preset)   | maintain the task ledger                                            |
| `speckit.implement`            | core (preset)   | iterate on the Experiment                                           |
| `speckit.research.epic`        | extension       | draft an Epic for a human to publish                                |
| `speckit.research.experiments` | extension       | propose the Experiments of a published Epic and create their issues |
| `speckit.research.approve`     | extension       | review a spec against its Epic as the independent party             |
| `speckit.research.run`         | extension       | prepare and launch a Formal Run                                     |
| `speckit.research.finish`      | extension       | close out an Experiment                                             |
| `speckit.research.synthesize`  | extension       | synthesize an Epic from the rendezvous                              |
| `speckit.research.status`      | extension       | show research status (read-only)                                    |

All three frameworks address them as `/speckit-research-run` (dots become hyphens in skill names). Spec Kit scripts find
the feature directory through `SPECIFY_FEATURE_DIRECTORY` or `.specify/feature.json` (gitignored), not the branch name.
`SPECKIT_PYTHON_EXECUTABLE` points at the root `.venv` python so template resolution has PyYAML.

## just recipes and scripts

| Recipe                            | Script                                                                                         | Exit codes                                         |
| --------------------------------- | ---------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| `just check`                      | lint + test + validate-records + `deno fmt --check` + `just --fmt --check` + ruff format check | non-zero on any failure                            |
| `just fmt`, `just lint`           | ruff format and check, `deno fmt`, `just --fmt` (fmt); ruff check (lint)                       |                                                    |
| `just test`                       | `uv run pytest scripts/tests`                                                                  |                                                    |
| `just validate-records`           | `scripts/run_record.py validate <records>`                                                     | non-zero on a schema violation, prints what to fix |
| `just budget <exp> [--reserve X]` | `scripts/budget.py`                                                                            | non-zero when over limit; `--json`                 |
| `just preflight <exp> <run>`      | `scripts/run_preflight.py` (`--skip-platform`); includes Epic validity and spec approval       | non-zero on any failed start condition             |
| `just epic-status <n>`            | `scripts/epic_status.py`                                                                       | 0 valid, 1 invalid (reasons), 2 unreachable        |
| `just spec-approval <exp>`        | `scripts/spec_approval.py`                                                                     | 0 approved, 1 missing, 2 unreachable               |
| `just status`                     | `scripts/research_status.py` (git + files only)                                                | read-only                                          |
| `just source-commit <exp> <run>`  | `scripts/source_commit.py` (`--verify-tracker`)                                                | 1 record never committed; mismatch reported        |
| `just tracker <exp> <run>`        | `scripts/tracker_lookup.py` (`--json`)                                                         | read-only                                          |
| `just outbound <paths>`           | `scripts/outbound_check.py`                                                                    | non-zero on findings; rule id + file:line only     |
| `just scan`                       | `scripts/outbound_check.py` over the working tree as git sees it, with `.gitleaks.toml`        | non-zero on findings                               |
| `just speckit-install`            | `specify preset add` + `specify extension add` (dev mode)                                      |                                                    |
| `just skills`                     | `npx skills` via deno                                                                          |                                                    |

Scripts are Python 3.12, stdlib + PyYAML, each with `main()` and argparse; helpers `scripts/_git.py`,
`scripts/_records.py`, `scripts/_gh.py`; tests in `scripts/tests/`. Platform scripts use `gh` read-only
(`gh api graphql` in `epic_status.py`, `gh pr list` in `spec_approval.py`; the Spec Kit commands use `gh issue view`),
retry three times with backoff, and never assume validity. `scripts/check_commit_message.py` and
`scripts/check_branch_scope.py` run as hooks; `scripts/source_commit.py` and `scripts/tracker_lookup.py` are called at
close-out by the finish command. `scripts/outbound_check.py` finds gitleaks on PATH or in the pre-commit cache (built by
`pre-commit install --install-hooks`, which the devcontainer runs); with neither it exits 2 and names that command as
the fix.

## pre-commit

`default_install_hook_types: [pre-commit, commit-msg, pre-push]`, `default_stages: [pre-commit]`;
`pre-commit install --install-hooks` (run by the devcontainer) installs all three and builds the hook environments.
Stages:

| Stage      | Hooks                                                                                                                                                                                                                                          |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| pre-commit | whitespace and EOF fixers, JSON/YAML/TOML checks, large files, private keys, ruff + ruff-format, `uv-lock` (root lock stays fresh), deno fmt/lint, `just --fmt --check`, gitleaks on staged changes, run-record validation, branch-scope check |
| commit-msg | `scripts/check_commit_message.py` (receives the message file as argv[1])                                                                                                                                                                       |
| pre-push   | `scripts/outbound_check.py --git-range` over the outgoing commits (`PRE_COMMIT_FROM_REF`..`PRE_COMMIT_TO_REF`)                                                                                                                                 |

gitleaks is pinned at `rev: v8.30.1`; pre-commit builds it with a bootstrapped Go toolchain on first use (minutes,
cached afterwards). A failing hook is fixed at its cause; `SKIP=` and `--no-verify` are not used.

## gitleaks

`.gitleaks.toml` starts with `[extend] useDefault = true` so the default secret rules stay active, then adds PII rules:
`restrict-non-anonymous-emails`, `restrict-public-ipv4`, `restrict-public-ipv6`, `restrict-home-paths`. Every `uv.lock`,
`pyproject.toml` and `*.requirements.txt` is allowlisted for the IPv4 rule only, because version strings look like
addresses. Direct CLI for arbitrary files:
`gitleaks dir <path> --config .gitleaks.toml --no-banner -f json -r
/dev/stdout`.

## uv

Root `pyproject.toml` is a virtual workspace (no build system): `[dependency-groups] dev = ["pytest>=8",
"pyyaml>=6"]`,
`[tool.uv.workspace] members = ["packages/*"]`. `uv sync` at the root installs the management tools;
`uv sync --all-packages` adds the libraries. Experiments are not members: each has its own `uv.lock`, path sources
`{ path = "../../packages/<lib>", editable = false }`, and is operated with `uv lock --project experiments/<id>` or from
inside the directory. A directory matched by `members` must hold a `pyproject.toml`. Export and image idioms:
`evidence.md`.

## Devcontainer

`.devcontainer/devcontainer.json`: CUDA base image, docker-in-docker, git, git-lfs, gh, deno, hf CLI, nvidia container
toolkit, uv with `pre-commit` and `rust-just`; `postCreateCommand` runs `uv sync && pre-commit install --install-hooks`;
`remoteEnv` sets `SPECKIT_PYTHON_EXECUTABLE` to the root `.venv` python (the `justfile` exports it as well). GPU is
optional on the host; a run that requests `gpu` fails preflight without one.

## Agent framework permission files

| Framework   | File                                         | Mechanism                                                                                          | Limit                                                                                           |
| ----------- | -------------------------------------------- | -------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Claude Code | `.claude/settings.json`                      | `permissions.deny` / `allow` with `Bash(git push *)` patterns; `CLAUDE.md` = `@AGENTS.md`          | prefix match; `git -C . push` or `sh -c` evade it; allow rules apply only after workspace trust |
| Codex       | `.codex/config.toml`, `.codex/rules/*.rules` | `sandbox_mode = "workspace-write"`, no network; `prefix_rule(pattern=[...], decision="forbidden")` | literal argv prefixes; project layer loads only for trusted projects                            |
| OpenCode    | `opencode.json`                              | `permission.bash` patterns; last matching rule wins, `*` first                                     | raw-string pattern match                                                                        |

All three allow `git push` to the agent's own branches, `gh issue view|list|create|comment`,
`gh pr view|list|create|edit|comment|merge`, `just`, `uv`, `docker build|run` and `pytest`; deny `git push --force` (and
`-f`, `--force-with-lease`), the usual spellings of a push to `main`, `docker push`,
`gh issue edit|close|reopen|delete`, `gh pr close|ready|review`, `gh label`, `gh repo edit|delete`, `gh secret` and
`gh ruleset`; `gh api` asks, because it can write anything. These lists catch slips; the token is the boundary. Skills:
project skills are canonical in `.agents/skills/<name>/SKILL.md` with `.claude/skills/<name>` a relative symlink to
them; Spec Kit skills are canonical in `.claude/skills/speckit-*/` with `.agents/skills/speckit-*` symlinks to them (see
Spec Kit above). Codex reads `.agents/skills/`, OpenCode reads `.claude/skills/`.

## GitHub

| File                                    | Role                                                                                                                               |
| --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `.github/labels.yml`                    | `epic`, `epic:approved`, `experiment`, `spec:approved`, `synthesis`; synced by `.github/workflows/labels.yml` (dry-run on PR)      |
| `.github/ISSUE_TEMPLATE/epic.yml`       | Epic form: objective, scope, constraints, budget policy, exit criteria                                                             |
| `.github/ISSUE_TEMPLATE/experiment.yml` | experiment issue form, including the allowance                                                                                     |
| `.github/PULL_REQUEST_TEMPLATE.md`      | one section per PR kind (experiment: runs, usage, deviations; synthesis: rendezvous, evidence, open questions); merge commits only |
| `.github/CODEOWNERS`                    | protected paths owned by the maintainer's login                                                                                    |
| `.github/workflows/secret.yml`          | TruffleHog over the commits a PR or a push to `main` adds; a platform-side backstop for secrets, after the local gitleaks hook     |
| `.github/workflows/ci.yml`              | backstop on push to `main` and on PRs: `uv sync`, `just check`, `pre-commit run --all-files`                                       |

Settings the owner configures by hand, which no file in the repository can set:

- Branch protection or a ruleset on `main`: require a pull request and review from code owners; merge commits only (no
  squash, no rebase), because run history must survive. Repository admins keep bypass, so a solo owner can merge harness
  PRs; who merged (`mergedBy`) is the audit signal.
- The agent's credential has no admin rights: a machine account with the write role, or a fine-grained token with
  `Contents: write` (push and merge), `Pull requests: write` and `Issues: write` and nothing wider (the same three at
  `read` when external writes are off). Whether a fine-grained token created by the admin's own account inherits the
  admin bypass is not verified here; a separate machine account avoids the question.
- The approving agent uses the same credential as the authoring agent. The platform therefore cannot tell who applied
  `spec:approved`; independence rests on the procedure (a fresh clean-context agent runs the approval). A second account
  or token for the approver is the upgrade when the platform must be able to tell.

Read-only queries: `gh api graphql` for the Epic's state, label events and `lastEditedAt` (`epic_status.py`),
`gh pr list --head <exp-id> --state open --json number,labels` (`spec_approval.py`), and
`gh issue view N --json parent,labels,state` in the Spec Kit commands. Writes the agent makes:
`gh issue create
--parent <epic>` for experiment issues, `gh pr create`,
`gh pr edit --add-label|--remove-label spec:approved`, `gh pr comment`, `gh issue comment`, `gh pr merge --merge`.
Experiment and synthesis PRs are merged with merge commits so `Merge pull request #N from ...` leads back to the PR.

## `.local/` layout

| Path                           | Content                                                       |
| ------------------------------ | ------------------------------------------------------------- |
| `.local/data/<input>/`         | fetched inputs; `VERSION` holds the declared version string   |
| `.local/runs/<exp-id>/<R###>/` | run outputs                                                   |
| `.local/trackio/`              | tracker storage, one `<project>.db` per experiment            |
| `.local/drafts/`               | outbound drafts: issues, PR bodies, comments, checkup reports |

Everything under `.local/` is gitignored and never leaves the machine.
