# Evidence chain

Read this before preparing, launching, finishing or verifying a Formal Run, and before declaring any number a result.
Source of truth for what a Formal Run must satisfy and leave behind. It fixes boundaries only; how to build and run is
the agent's choice. Container, lock-file and image details below are the machine-learning example.

## Four anchors

| Question           | Anchor                                            | Fixed where                                                                    |
| ------------------ | ------------------------------------------------- | ------------------------------------------------------------------------------ |
| which question     | the approved spec version                         | `spec_digest` in the run record; approval on the Experiment's PR               |
| which code         | the source commit: first commit on the run branch | the branch structure; the hash recorded in the tracker                         |
| which dependencies | frozen manifest with hashes                       | committed with the source commit                                               |
| which data         | source and immutable version of every input       | `data` entries in the run record; `VERSION` marker in the local data directory |

The anchors fix inputs. Results live in one tracker record, found through the run record's `tracker` reference.

## Run branch procedure (order is not negotiable)

Every Formal Run happens on its own branch; the branch structure itself records which commit ran.

1. Branch `run/<exp-id>/R###` from the Experiment branch `<exp-id>`. Pick the next number counting unmerged run branches
   too; retries get a new number.
2. Write `experiments/<exp-id>/runs/R###.yaml`: what the run decides, command, parameter source, data, resources,
   maximum duration, environment definition, reservation (schema below; start from `template/run-record.yaml`).
3. Make sure the frozen manifest `experiments/<exp-id>/requirements.txt` matches the environment this run needs
   (`just freeze <exp-id> [backend]` when dependencies changed since it was last frozen).
4. Commit the record, the manifest when it changed, and any inputs specific to this run. This is the first commit on the
   run branch: the **source commit**.
5. Confirm the start conditions (`just preflight <exp-id> R###`).
6. Run, using only the source commit's content, and record the source commit hash in the tracker. How to build and
   launch is the agent's choice.
7. After the run, commit on the run branch: the outcome, actual usage and the result files to keep.
8. Merge the run branch into the Experiment branch with a merge commit (`git merge --no-ff`). The party that ran it
   merges; no pull request.

Source commit lookup: `git log --diff-filter=A --format=%H -- experiments/<exp-id>/runs/R###.yaml`
(`scripts/source_commit.py <exp-id> R###`; `--verify-tracker` compares with the tracker's `source_commit`), valid after
the branch is deleted. Close-out verifies that every completed run is in the tracker with the same hash.

Run-branch rules:

- Merge with a merge commit, never fast-forward: a fast-forward erases the run branch from the structure.
- Completed, failed and aborted runs are all merged back; a run cancelled before start is recorded `aborted` and merged
  too. Records are never deleted; their usage stays in the budget. Sole exception: an Experiment abandoned before
  merging into `main` may drop its branch, after writing actual usage back to the experiment issue.
- Before start the run branch holds exactly the source commit. Until then it may be redone: amend it or recreate the
  branch under the same number when dependencies or inputs change.
- After start, only results are appended. Different inputs mean a new run on a new branch.
- Budget checks and status reports count unmerged run branches (`git show <branch>:<path>`).
- The `run/` prefix exists because Git forbids a branch name that is a directory prefix of another branch.

## Start conditions

Confirmed by the party that runs, normally the agent; `just preflight <exp-id> R###` checks the mechanical ones and
prints what to fix. Any failure means no launch:

- no uncommitted change that could affect the run;
- record and manifest committed; the run branch holds exactly one commit beyond the Experiment branch;
- the manifest matches what will be installed;
- the spec has a valid approval (`just spec-approval <exp-id>`) and `spec_digest` matches the spec at the source commit;
  a spec edited after approval has no valid approval until it is approved again (`governance.md`, Spec approval);
- the Epic is valid (`just epic-status <n>`);
- the budget fits (`just budget <exp-id> --reserve <x>`);
- every declared input is present and `.local/data/<name>/VERSION` equals the declared version;
- requested resources are available (`gpu` → `nvidia-smi` succeeds).

## Run record

One small YAML file per run, validated by `just validate-records` (`scripts/run_record.py validate`). The schema, with
every field annotated, is `template/run-record.yaml`; copy it and fill in every field. Two groups of fields:

- **Definition fields**, frozen at the source commit: `id`, `experiment`, `decision` (one sentence: what this run
  decides), `command` (what was run; how it is launched is the agent's choice), `params_source` (`git` | `tracker` |
  `mixed`, the single authority for the run's parameters) and `params_path`, `data` (name, source, immutable `version`,
  local path per input), `resources`, `max_duration` (ISO-8601; exceeding it means `aborted`), `environment`
  (Dockerfile, lockfile, hashed requirements manifest), `budget.reserved` (omitted when the spec has no `budget` block),
  `spec_digest` (SHA-256 of `specs/<id>/spec.md` at the source commit) and `tracker` (project and run name).
- **Exactly five execution fields**, written after the run: `outcome` (`completed` | `failed` | `aborted`),
  `execution_ref` (container id, job id, free text), `failure_reason`, `actual_usage` (in the spec's unit; failed and
  aborted runs record what they consumed; never started is 0) and `interruptions` (resume-from-own-checkpoint count).

Validator rules: relative repo paths only (no `/home/`, `/Users/`, `C:\`, hostnames, `user@`), so records stay portable
and survive the repository going private; `version` values are not `latest`, dates or branch-like; `outcome` in the
enum; `reserved` and `actual_usage` numeric; every data entry complete.

Record rules:

- Only terminal states exist: `completed`, `failed`, `aborted`. "Not started" and "running" are read from the branches:
  record without outcome on an unmerged run branch = not started or running; outcome present and merged = finished. The
  outcome is written once, truthfully; a run killed at `max_duration` is `aborted`.
- A retry is a new record with a new number; the failed one stays.
- Resuming from the run's own checkpoint after an interruption is the same run (source commit, environment and
  checkpoint unchanged): increment `interruptions`, continue the same tracker record, budget counted once. A checkpoint
  from another run makes a new run and is declared as an input.
- A sweep is one Formal Run with several tracker trials; narrowing the space after seeing results is a new Formal Run.
- No metrics and no conclusions in the record: metrics live in the tracker, interpretation in the README.

## Runtime boundaries

However the run is launched, all of these hold: code comes only from the source commit; declared data is read and never
modified; outputs go to a location specific to this run (`.local/runs/<exp-id>/R###/`); wall time, cumulative across
resumes, stays within `max_duration` or the run is terminated and recorded `aborted`; unavailable resources mean the run
does not start with a report. Outputs stay local; small result files the README cites are copied into the Experiment
directory and reviewed like any outbound content.

ML example: a container with the source commit's `git archive` and each input directory read-only, the run's output
directory and the tracker directory read-write, a tmpfs, no network, no home directory, the caller's user id, and the
source commit, paths and tracker reference passed as environment variables.

## No silent degradation

A requested resource that is unavailable means the run does not start. GPU requested, GPU unusable: fail and report;
never fall back to CPU or another host, because the numbers would then disagree with the recorded conditions. Switching
resources is a new decision, recorded in a new run record.

## Environment frozen per Experiment

Boundaries: every Formal Run's environment is pinned item by item in a hashed manifest that is part of the source
commit, one file per Experiment (`experiments/<exp-id>/requirements.txt`), regenerated only when dependencies change:
the source commit fixes which version of it a run installed, so no copy per run is kept; the environment belongs to the
Experiment, which has its own lock and is not a member of the root workspace; an environment changed after freezing
voids the freeze, so re-freeze and redo the source commit for a run not yet started, never reinstall and continue.
Reason: preprocessing, training and reproduced third-party code conflict down to system libraries, and separate locks
keep parallel Experiments from editing one shared file.

Shared by default: an Experiment owns its lock file, and the content of that file is the project baseline
(`template/experiment/`: `pyproject.toml`, `uv.lock`, `requirements.txt`) unless the plan states why this Experiment
needs something else. The same holds for the base image and tool versions. When the baseline lacks a dependency, reuse
the lock of an earlier Experiment that has it before resolving anything new; when you add one, keep every existing pin
(`uv lock`, never `--upgrade`). A difference without a stated reason is a defect: each distinct manifest costs a full
install, an image layer or a venv of its own, and one more variable between Experiments that are compared. Dependencies
that several Experiments added are moved into the baseline in the next preparation phase.

Install once per manifest, in every execution environment: whatever is installed is keyed by the manifest's content, not
by the run or the Experiment, so a run whose manifest is unchanged installs nothing, and a code change never triggers an
install. In a container, dependencies and source are separate layers, dependencies first, and nothing that varies per
run (run ID, source commit, the source tree) is visible to the dependency layer. Without a container, the manifest is
installed with `--require-hashes` into a venv named after the manifest's digest (for example
`.local/envs/<first 12 hex of its sha256>/`), created once, reused by every run with that manifest, and never modified
afterwards; a changed manifest gets a new venv.

Default image, as a template (`template/experiment/Dockerfile` is the same shape; any image that keeps the boundaries is
fine). Two steps, in this order:

```dockerfile
FROM <base image, pinned>
# installer, pinned

# 1. Dependencies. Only the frozen manifest is visible here; install it for the environment the run needs.
RUN --mount=<manifest> --mount=<installer cache> \
    uv pip install --system --require-hashes --no-deps --torch-backend=cuXXX -r <manifest>

# 2. Source. The only step whose input changes from one round to the next.
COPY . /app/
```

Why this order: across the rounds of an Experiment, and across Experiments on the same baseline, nothing step 1 reads
changes, so everything up to and including the dependencies comes from the build cache and a rebuild only copies the
source. Whatever would change per run (run ID, source commit, the source tree) stays out of step 1; a build argument in
scope of the install step counts, because its value is part of that step's cache key. Check once per Experiment: a
second build after a source-only change reports the install step as `CACHED`.

Fitting the environment: a run that needs a GPU names its accelerator backend exactly, `--torch-backend=cuXXX` for
PyTorch (`cpu` for a CPU run), chosen to match the driver of the machine that executes the run. Never `auto` and never
the installer's default: both are decided by the machine that builds, which may have no GPU, and the result is a silent
change of backend (see No silent degradation). The first thing the run does is fail if the requested accelerator does
not start. A project without PyTorch drops the option.

Freezing the manifest: `just freeze <exp-id> [backend]` writes `experiments/<exp-id>/requirements.txt` from the
Experiment's `pyproject.toml` and `uv.lock`; run it when dependencies or the backend change and commit the result with
the lock. Every Experiment uses this one recipe, so equal dependencies give equal files. The backend is part of what is
frozen, because the same version has different files and hashes per backend: with a backend the recipe compiles the
manifest with the option the image installs with, constrained to the versions in the lock,

```sh
uv export --format requirements.txt --locked --no-dev --no-emit-project --no-emit-local --no-hashes -o <pins>
uv pip compile pyproject.toml --constraint <pins> --torch-backend=cuXXX --generate-hashes --no-header --no-annotate -o requirements.txt
```

and without one it exports the lock as it is:

```sh
uv export --format requirements.txt --locked --no-dev --no-emit-project --no-emit-local --no-header --no-annotate -o requirements.txt
```

`--no-header` and `--no-annotate` drop the comments that repeat the command line and the project name, so manifests of
the same dependencies are byte-identical across Experiments and share one installed layer. A manifest frozen for one
backend installs only with that backend: without the option, or with another, the install fails on a missing version or
a hash mismatch, which is the intended result. Shared libraries are path dependencies
`{ path = "../../packages/<lib>", editable = false }`; they are left out of the manifest (`--no-emit-local`, they carry
no hash), built as wheels with `uv build --package <lib>` from the root, and installed in a step of their own between
the two above.

## Data and external inputs

Data stays out of Git. Every external input a run reads, pretrained weights included, is declared beforehand with a
source and an exact version: a commit hash, a file SHA-256, a manifest digest; `latest`, a date or a mutable branch is
not a version. An input is in place only after it is fetched into `.local/data/<name>/` and verified; its declared
version goes into `.local/data/<name>/VERSION`. Very large data may be verified once at fetch time using the provider's
own content identifier, stated in the README. Before adding an input settle licence, redistribution, provenance, and
whether the reference itself leaks anything; inputs within the Epic's allowed sources and licences are added without
asking, others stop this Experiment pending the owner. Run records are published with the repository, so bucket names,
internal addresses and accounts stay out: use a neutral alias and keep the real location in a gitignored local file.

## Tracker

Experiment code calls the tracker directly; there is no wrapper. Four requirements: the run record's tracker reference
finds the Formal Run; every tracker record names its Formal Run and source commit; both are readable by script; the
authority for the run's parameters is clear (`params_source`: `git` means a file in the source commit, the tracker
config is a copy; `tracker` means the tracker config, with no second copy in Git; `mixed` means Git holds what the
tracker lacks, with the split stated). With local tracker storage prefer `git`, since local tracker data does not travel
with the repository.

Trackio example: project = experiment id, run name = `R###`, `config` includes `formal_run: "<exp-id>/R###"` and
`source_commit: "<sha>"`; pass `auto_log_cpu=False, auto_log_gpu=False` unless wanted. Offline environment:
`TRACKIO_DIR=.local/trackio`, `HF_HUB_OFFLINE=1`, `TRACKIO_STORAGE_MODE=sqlite`, and none of `TRACKIO_SPACE_ID`,
`TRACKIO_SERVER_URL`, `TRACKIO_BUCKET_ID`, `TRACKIO_DATASET_ID`. The config row is written on the first `log()`. Read
back with plain `sqlite3` on `.local/trackio/<project>.db`:
`SELECT run_id, run_name, config FROM configs WHERE json_extract(config,'$.formal_run')=?` (`config` is JSON bytes);
metrics: `SELECT step, metrics FROM metrics WHERE run_id=? ORDER BY step`. `scripts/tracker_lookup.py <exp-id> R###`
does this.

## Limits of the chain

Reproduction means returning to the source commit's snapshot; the project does not keep old Experiments running in later
environments, and edited old code counts only after it is run again. Rebuilding years later may fail when base images or
wheels vanish from their sources. Local tracker storage survives only on this machine, so the key numbers behind a
conclusion are copied into the README with their Formal Run named. Held-out data staying untouched is discipline fixed
in each spec's `holdout`; no machine check exists. Changing where runs execute changes only the method: everything above
stays, and shipping code, building, submitting and fetching results are the agent's to design for the new place.
