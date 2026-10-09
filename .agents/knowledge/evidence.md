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
3. Freeze the environment and export the hashed manifest `experiments/<exp-id>/runs/R###.requirements.txt`.
4. Commit the record, the manifest and any inputs specific to this run. This is the first commit on the run branch: the
   **source commit**.
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

Boundaries: every Formal Run's environment is pinned item by item in a hashed manifest committed with the source commit;
the environment belongs to the Experiment, which has its own lock and is not a member of the root workspace; an
environment changed after freezing voids the freeze, so re-freeze and redo the source commit for a run not yet started,
never reinstall and continue. Reason: preprocessing, training and reproduced third-party code conflict down to system
libraries, and separate locks keep parallel Experiments from editing one shared file.

ML example (`template/experiment/` is the starter): the Experiment has its own `Dockerfile`, `pyproject.toml` and
`uv.lock`; shared libraries are path dependencies `{ path = "../../packages/<lib>", editable = false }`; the base image
is pinned to a digest or explicit tag. Export per run, from the Experiment directory:

```sh
uv export --format requirements.txt --locked --no-dev --no-emit-project --no-emit-local -o runs/R###.requirements.txt
```

`--no-emit-local` drops path dependencies because they export without hashes; build shared libraries as wheels with
`uv build --package <lib>` from the root and install them separately. In the image:

```dockerfile
COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /uvx /bin/
RUN uv pip install --system --require-hashes --no-deps -r R###.requirements.txt \
 && uv pip install --system --no-deps ./<lib>-<version>-py3-none-any.whl
```

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
stays, and shipping code, building, submitting and fetching results are the agent's to design for the new place
(`adaptation.md`).
