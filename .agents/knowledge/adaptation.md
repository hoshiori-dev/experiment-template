# Adapting the template

The `adapt-template` skill runs the adaptation and reads this file for the decisions. Read it directly when turning the
template into a real project, when the owner asks what can be changed and at what cost, or when a run must execute
somewhere other than local Docker. Each decision is the owner's; the agent lays out status, options and costs.
Alternatives marked **untested** have adaptation notes only and have never been run with this harness.

## Decisions to make first

| Decision                  | Shipped value                                             | Alternatives and what changes                                                                                                                                                                                                                                                             |
| ------------------------- | --------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Governance model          | high-automation                                           | human-led: humans create experiment issues, a human approves each spec and merges each experiment PR; external writes may stay on or go off. Switch by flipping the three permission files, AGENTS.md "Current settings", the `(current)` column in `governance.md` and the README table. |
| Budget unit               | set per Epic (`gpu-hours` in examples)                    | any label: compute units, currency, node-hours; checks compare numbers only. "Unlimited" is written in the Epic, so the spec has no `budget` block and records no `reserved`.                                                                                                             |
| Epic-level hard cap       | approver check                                            | machine-enforced: a script must read every Experiment's spec cap and issue usage; not shipped.                                                                                                                                                                                            |
| Repository visibility     | public, public-repo publishing standard                   | private in a controlled environment: keep the secret scan and the no-secrets rule, drop the extended PII rules and the agent read-through. Going public later means reviewing the whole history first.                                                                                    |
| External writes           | on                                                        | off: deny push and the `gh` write commands in the three permission files; the agent drafts to `.local/drafts/` and a human posts. Turning it on again needs the platform prerequisites in `tooling.md` (GitHub) first; either switch is a protected-file change merged by the owner.      |
| Agent attribution         | forbidden (instruction, Claude Code setting, commit hook) | allowed: remove the `attribution` block in `.claude/settings.json` and relax `scripts/check_commit_message.py`; the responsibility argument in `governance.md` still applies.                                                                                                             |
| Commit address            | platform noreply only                                     | open: relax the hook's author check and the email rule in `.gitleaks.toml`; fits internal deployments.                                                                                                                                                                                    |
| Owner handle              | the template author's login in `.github/CODEOWNERS`       | replace every occurrence with the maintainer's GitHub login before enabling code-owner review; the file is also the list of protected paths.                                                                                                                                              |
| Approval-label automation | off                                                       | on: a workflow that removes `spec:approved` when `specs/<id>/spec.md` changes and rejects author-applied labels; mind fork PR permissions.                                                                                                                                                |

Also at creation: write the project's own `README.md` and `README.zh.md`, set `.specify/memory/constitution.md` (keep
the five principles unless the owner changes the design), and configure the platform settings listed in `tooling.md`.
`just speckit-install` is needed only after editing `speckit/`.

## Execution environment

Fixed everywhere: run branch and source commit, start conditions, runtime boundaries, per-Experiment frozen environment,
declared data with immutable versions, tracker contents (`evidence.md`). The agent decides how code gets there, how it
is built, how the job is submitted and how results come back; the run record's `command`, `execution_ref` and
`environment` describe it.

| Environment                                           | What stays fixed                                                                                         | Agent decides                                                                                                                    | Status   |
| ----------------------------------------------------- | -------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | -------- |
| local Docker, CPU or one GPU                          | everything above                                                                                         | image build, mounts, env vars                                                                                                    | shipped  |
| other container hosts (Podman, Apptainer/Singularity) | same; read-only code and data, run-specific output                                                       | image format conversion, rootless mapping, bind mounts                                                                           | untested |
| cluster schedulers (Slurm, PBS, Kubernetes)           | same; `execution_ref` = job id; `max_duration` = requested wall time; `resources` = requested allocation | shipping the source commit archive, module or container loading, job script, fetching outputs and tracker data back to `.local/` | untested |
| cloud jobs (managed training services)                | same; data via a declared immutable object version; no silent instance substitution                      | job definition, credentials kept out of Git, cost unit mapping to the budget                                                     | untested |
| no container (bare venv on a trusted host)            | same; manifest installed with `--require-hashes` into a fresh venv; code from `git archive`              | isolation substitutes for mounts; network access documented in the README                                                        | untested |

A run that cannot meet a boundary in its environment (for example a scheduler that silently moves the job to another
accelerator) is not a Formal Run there; record it `aborted` with the reason, or pick another environment.

## Tracker

Any tracker meeting the four requirements in `evidence.md` works: findable from the run record's reference, names its
Formal Run and source commit, readable by script, parameter authority clear. Trackio with local storage is shipped. For
a remote or hosted tracker, syncing is an external write and follows that setting; the run record's `tracker` block then
holds the project and run identifiers the service uses, and `scripts/tracker_lookup.py` needs a replacement that reads
the service. **Untested**: MLflow (local file store satisfies the requirements through `mlflow.set_tag` for `formal_run`
and `source_commit`), Weights & Biases (config keys the same; hosted, so external writes apply), TensorBoard alone (no
config store, so `params_source: git` is mandatory and `formal_run` goes into the log directory name).

## GitLab (untested)

Epics become issues with the `epic` label (or GitLab epics on tiers that have them; the scripts assume issues),
experiment issues are related issues or tasks, approval is a merge request label `spec:approved`, synthesis is a merge
request with label `synthesis`. `glab` replaces `gh` in `scripts/epic_status.py` and `scripts/spec_approval.py`
(`glab issue view`, `glab mr list --source-branch <exp-id>`, `glab api`); the label-after-creation check needs the
resource label events endpoint. Protected branches and code-owner approval (`CODEOWNERS` with approval rules) take the
place of GitHub branch protection. Merge commits remain mandatory: no squash, no fast-forward. The gitleaks email rule
already accepts `noreply.gitlab.com` addresses.

## What does not change

Both human gates; shared part changed only in preparation and merged by humans; budget caps set by humans; the agent
never loosens its own rules and checks; the five forbidden content classes and the three confidentiality rules; English
for code and agent-facing files.
