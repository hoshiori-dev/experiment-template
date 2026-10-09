---
name: speckit-research-run
description: Execute a Formal Run - run branch, run record, frozen environment, source commit, preflight, merge back.
compatibility: Requires spec-kit project structure with .specify/ directory
metadata:
  author: experiment-template
  source: research:commands/speckit.research.run.md
---

## User Input

```text
$ARGUMENTS
```

## Role and goal

You execute one Formal Run: one research decision plus one reproducible launch that produces evidence. The eight steps
below are ordered and the order is fixed; how you build and run inside step 6 is your choice. Read
`.agents/knowledge/evidence.md` before starting: it holds the run record schema, the four anchors a run must fix, and
the runtime boundaries. The annotated record is `template/run-record.yaml`.

## Steps

1. **Preconditions and run ID.** `$ARGUMENTS` names the Experiment `<id>` (`exp-NNN-<slug>`; its short form `exp-NNN` is
   the commit scope) and the decision this run makes; ask for what is missing. Confirm `git branch --show-current` is
   `<id>` and `git status --porcelain` is empty. Read the Epic number `P` once, read-only:
   `gh issue view N --json parent` with `N` the `issue` field of `specs/<id>/spec.md` front matter. Allocate `R###` as
   one more than the highest number among `experiments/<id>/runs/R*.yaml` and the branches
   `git branch --all --list 'run/<id>/R*'`; retries get a new number. Done when: `<id>`, `P`, the decision sentence and
   a free `R###` are known.

2. **Run branch.** `git switch -c run/<id>/R### <id>`. Done when: the branch exists and points at the Experiment branch
   tip.

3. **Run record.** Write `experiments/<id>/runs/R###.yaml` with the definition fields only: `id`, `experiment`,
   `decision`, `command`, `params_source` (`git` | `tracker` | `mixed`) and `params_path` when git or mixed, `data`
   (each input: `name`, `source`, immutable `version`, `path` under `.local/data/`), `resources` (`accelerator`,
   `count`), `max_duration` (ISO-8601), `environment` (`dockerfile`, `lockfile`, `requirements`), `budget.reserved` in
   the spec's unit (omit when the spec has no budget block), `spec_digest` (`sha256:` + `sha256sum specs/<id>/spec.md`),
   `tracker` (`project: <id>`, `run: R###`). Paths are repository- relative; versions are content identifiers, never
   `latest`, a date or a branch. Done when: `just validate-records` passes on the new file.

4. **Freeze the environment.** Machine-learning example: `experiments/<id>/` has its own `pyproject.toml`, `uv.lock` and
   `Dockerfile` with a pinned base image; inside `experiments/<id>/`, export the hashed manifest:
   `uv export --format requirements.txt --locked --no-dev --no-emit-project --no-emit-local
   -o runs/R###.requirements.txt`.
   Any other kind of experiment records whatever manifest pins its environment item by item, at the path named in
   `environment.requirements`. Done when: the manifest named in the record exists and matches what the run will install.

5. **Source commit.** Run `just epic-status P` first: exit 0 continues; exit 1 (invalid Epic) stops the Experiment
   (`/speckit-implement` Stopping) before any commit; exit 2 (platform unreachable) waits and retries. Then
   `git add experiments/<id>/runs/R###.yaml experiments/<id>/runs/R###.requirements.txt` plus any input specific to this
   run (configs, split files), and commit with title `exp-NNN: R### source`. This is the only commit on the run branch
   before the start; while nothing has started, amend it or recreate the branch under the same number when inputs
   change. Then run `just preflight <id> R###`, which checks the start conditions including spec approval and Epic
   validity (add `--skip-platform` only when the platform is unreachable and approval and Epic were verified earlier in
   this session). Every failure names what to fix; fix it in the source commit and run the preflight again. Done when:
   `just epic-status P` and `just preflight <id> R###` both exit 0.

6. **Run.** Immediately before launch, run `just epic-status P` and `just preflight <id> R###` once more; an invalid
   Epic or a failed preflight stops the launch, and nothing starts until both exit 0. Only the source commit's content
   runs; take it from `git archive HEAD` or an equivalent, never from the working tree. Pass the source commit hash
   (`git rev-parse HEAD`) into the tracker: Trackio example with `TRACKIO_DIR=.local/trackio`, `HF_HUB_OFFLINE=1`,
   `TRACKIO_STORAGE_MODE=sqlite`, and
   `trackio.init(project="<id>", name="R###", config={"formal_run": "<id>/R###", "source_commit": "<sha>", ...})`.
   Outputs go to `.local/runs/<id>/R###/`; declared data is read-only; the run stops at `max_duration` and is recorded
   as `aborted`; an unavailable requested resource stops the run with a report, never a quiet fallback. The
   machine-learning example launches a container with no network, the archive and data mounted read-only, the output and
   tracker directories read-write; any launcher that keeps these boundaries is acceptable. Done when: the process has
   ended and the tracker holds the run.

7. **Result commit.** Add the five execution fields to the record: `outcome` (`completed` | `failed` | `aborted`),
   `execution_ref`, `failure_reason` (empty unless failed or aborted), `actual_usage` in the spec's unit (what was
   consumed, even on failure; a run that never started records 0 and `aborted`), `interruptions`. Copy the small result
   files the README will cite into `experiments/<id>/` (never raw logs, checkpoints or data). Commit with title
   `exp-NNN: R### <outcome>`. `just tracker <id> R###` prints the tracker record (config and metrics summary) for the
   `execution_ref` and the numbers the README will quote; `just source-commit <id> R### --verify-tracker` confirms the
   tracker's `source_commit` equals the commit that added the record. Done when: `just validate-records` passes, the
   verification prints a match, and the run branch has exactly two commits beyond `<id>`.

8. **Merge back.** `git switch <id>` then `git merge --no-ff run/<id>/R###`; the merge commit keeps the branch structure
   that records which commit ran. Then `just validate-records` and `just budget <id>`. Add a ledger row or note in
   `specs/<id>/tasks.md` naming `R###` and its outcome. The run branch may be deleted after the merge; the source commit
   stays findable by the commit that added the record. Done when: `git log --oneline --graph -5` shows the merge and
   both checks pass.

## Stop points

- Preflight fails for approval (exit 1): the spec has no valid label; the human or approver acts next.
- Epic invalid (`just epic-status P` or the preflight exits 1 for the Epic): nothing launches; finish nothing new,
  report to the human (`/speckit-implement` Stopping).
- Preflight fails for budget: the reserved amount does not fit; reduce `max_duration`/`reserved` honestly or stop the
  Experiment (`/speckit-implement` Stopping).
- Platform unreachable (exit 2): wait and retry; never assume approval.
- Interrupted run: resume from its own checkpoint only, with the same source commit and environment, and count it in
  `interruptions`; any other restart is a new run with a new number.
