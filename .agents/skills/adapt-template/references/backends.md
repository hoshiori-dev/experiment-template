# Backends: execution environment, tracker, platform

Load this when the owner's answers point to another place where runs execute, another tracker, or another hosting
platform. It states what stays fixed and what has to be built. These are notes, not a record of use: which option a
project uses is read from the repository (decisions.md), and which options a Formal Run has never exercised is listed
in `README.md` ("Not implemented or untested").

## Execution environment

Fixed everywhere: run branch and source commit, start conditions, runtime boundaries, the environment frozen per
Experiment and installed once per manifest, declared data with immutable versions, tracker contents
(`.agents/knowledge/evidence.md`). The agent decides how code gets there, how it is built, how the job is
submitted and how results come back; the run record's `command`, `execution_ref` and `environment` describe it.

| Environment                                           | What stays fixed                                                                                                   | Agent decides                                                                                                                    |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------- |
| local Docker, CPU or one GPU                          | everything above                                                                                                   | image build, mounts, env vars                                                                                                    |
| other container hosts (Podman, Apptainer/Singularity) | same; read-only code and data, run-specific output                                                                 | image format conversion, rootless mapping, bind mounts                                                                           |
| cluster schedulers (Slurm, PBS, Kubernetes)           | same; `execution_ref` = job id; `max_duration` = requested wall time; `resources` = requested allocation           | shipping the source commit archive, module or container loading, job script, fetching outputs and tracker data back to `.local/` |
| cloud jobs (managed training services)                | same; data via a declared immutable object version; no silent instance substitution                                | job definition, credentials kept out of Git, cost unit mapping to the budget                                                     |
| no container (bare venv on a trusted host)            | same; manifest installed with `--require-hashes` into a venv keyed by the manifest digest; code from `git archive` | isolation substitutes for mounts; network access documented in the README                                                        |

A run that cannot meet a boundary in its environment (for example a scheduler that silently moves the job to
another accelerator) is not a Formal Run there; record it `aborted` with the reason, or pick another environment.

What to change: the example passages in `.agents/knowledge/evidence.md`, the starter under `template/`, the
example in `speckit/extension/commands/speckit.research.run.md`, and the Execution environment row of AGENTS.md
"Current settings". The boundaries in `evidence.md` do not change.

## Tracker

Any tracker meeting the four requirements in `.agents/knowledge/evidence.md` works: findable from the run record's
reference, names its Formal Run and source commit, readable by script, parameter authority clear.

- Trackio with local SQLite storage.
- A remote or hosted tracker: syncing is an external write and follows that setting; the run record's `tracker`
  block holds the project and run identifiers the service uses.
- MLflow: a local store under `.local/` can satisfy the requirements with `formal_run` and `source_commit` as run
  tags; confirm the storage backend and the tag API against the version being locked before proposing it.
- Weights & Biases: the same config keys; hosted, so external writes apply.
- TensorBoard alone: no config store, so `params_source: git` is mandatory and `formal_run` goes into
  the log directory name.

Runs already recorded keep their tracker: their evidence stays where it was written, and the lookup must still reach
it, or the README of each finished Experiment must already carry the cited numbers.

What to change: `scripts/tracker_lookup.py` (replace it with one that reads the new tracker, keeping the exit codes in
`scripts/README.md`), the scripts that import it, their tests, the `just tracker` recipe if arguments change, the tracker examples in
`evidence.md` and `template/run-record.yaml`, and the Tracker row of AGENTS.md "Current settings".

## Platform other than GitHub (GitLab notes)

Epics become issues with the `epic` label (or GitLab epics on tiers that have them; the scripts assume issues),
experiment issues are related issues or tasks, approval is a merge request label `spec:approved`, synthesis is a
merge request with label `synthesis`. `glab` replaces `gh` in `scripts/epic_status.py` and
`scripts/spec_approval.py` (`glab issue view`, `glab mr list --source-branch <exp-id>`, `glab api`); the
label-after-creation check needs the resource label events endpoint. Protected branches and code-owner approval
(`CODEOWNERS` with approval rules) take the place of GitHub branch protection. Merge commits remain mandatory: no
squash, no fast-forward. Check that the email rule in `.gitleaks.toml` accepts the platform's noreply addresses; changing it is an owner decision.

What to change: `scripts/_gh.py` and the two scripts above with their tests, `.github/` (templates, labels,
workflows move to the platform's equivalents), the platform commands in the agent permission files and in the Spec
Kit commands, `.agents/knowledge/tooling.md` (platform section), and the Platform row of AGENTS.md "Current
settings".
