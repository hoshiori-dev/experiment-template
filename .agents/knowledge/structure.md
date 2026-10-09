# Structure and conventions

Read this before creating a file or directory, naming an Experiment, run or task, creating or merging a branch, or
writing a commit message. Source of truth for where things live and who merges them; `governance.md` says why.

## Directories

| Path                      | Holds                                                                                                                                 | Merged by        | Changed in      |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ---------------- | --------------- |
| `AGENTS.md`               | entrypoint: always-on rules, what to read when, commands, directories, current settings                                               | human            | preparation     |
| `CLAUDE.md`               | one framework's entrypoint; contains only `@AGENTS.md`                                                                                | human            | preparation     |
| `.agents/knowledge/`      | harness knowledge: rules, constraints and facts useful for development, one topic per file                                            | human            | preparation     |
| `.agents/skills/`         | procedures: step-by-step instructions for agents (canonical location)                                                                 | human            | preparation     |
| `.claude/`                | Claude Code settings and permissions; `.claude/skills/<name>` symlinks into `.agents/skills/`                                         | human            | preparation     |
| `.codex/`                 | Codex config and command rules                                                                                                        | human            | preparation     |
| `opencode.json`           | OpenCode config and permissions                                                                                                       | human            | preparation     |
| `speckit/`                | source of the research preset and extension (templates, commands)                                                                     | human            | preparation     |
| `.specify/`               | Spec Kit working directory: installed copies, its scripts and templates, the constitution; committed except the local feature pointer | human            | preparation     |
| `justfile`                | one recipe per action: check, format, scan, status, platform queries                                                                  | human            | preparation     |
| `scripts/`                | check scripts: record validation, outbound check, Epic status, budget, preflight                                                      | human            | preparation     |
| `scripts/tests/`          | tests of the scripts and of harness files                                                                                             | human            | preparation     |
| `.pre-commit-config.yaml` | hooks at commit, commit-msg and push                                                                                                  | human            | preparation     |
| `.gitleaks.toml`          | scanner rules                                                                                                                         | human            | preparation     |
| `pyproject.toml`          | root workspace: management-tool dependencies; members are `packages/*`; experiments excluded                                          | human            | preparation     |
| `uv.lock`                 | root workspace lock; no run installs from it                                                                                          | human            | preparation     |
| `.devcontainer/`          | dev container with all tools above                                                                                                    | human            | preparation     |
| `.github/`                | issue forms, PR template, labels, CODEOWNERS, CI                                                                                      | human            | preparation     |
| `template/`               | Experiment starter: `template/experiment/`, `template/run-record.yaml`                                                                | human            | preparation     |
| `packages/<name>/`        | one shared library: own `pyproject.toml`, own tests                                                                                   | human            | preparation     |
| `docs/`                   | accepted experimental knowledge                                                                                                       | human            | preparation     |
| `specs/<id>/`             | how one Experiment is coordinated: `spec.md`, `plan.md`, `tasks.md`                                                                   | governance model | experimentation |
| `experiments/<id>/`       | what one Experiment produced: `README.md`, code, config, own `pyproject.toml`, environment, results, tests                            | governance model | experimentation |
| `experiments/<id>/runs/`  | `R###.yaml` records and `R###.requirements.txt` manifests                                                                             | governance model | experimentation |
| `reports/`                | deliverables for people: papers, reports                                                                                              | human            | reporting       |
| `demos/`                  | demonstrations                                                                                                                        | human            | reporting       |
| `.local/`                 | gitignored: `data/<input>/` (+`VERSION`), `runs/<exp-id>/<R###>/`, `trackio/`, `drafts/`                                              | not in Git       | any time        |

Agent files plus tools and checks are the harness; with `packages/` and `docs/` they form the shared part. `docs/`,
`packages/`, `reports/` and `demos/` exist from the start, held by a `.gitkeep`, and stay empty until there is content
for them. "Governance model": human in human-led, agent in high-automation.

## Seven ideas behind the table

1. **Shared part and experiments change separately.** Experimentation touches only `specs/<id>/` and
   `experiments/<id>/`, each Experiment its own directories, so parallel commits rarely conflict. The pre-commit hook
   `scripts/check_branch_scope.py` enforces this on `exp-NNN-*` and `run/` branches.
2. **Coordination and output live apart.** `specs/` records process, `experiments/` keeps results; the README must stand
   alone when `specs/<id>/` is gone.
3. **Optional directories appear with real content.** A new Experiment needs only `README.md`; `src/`, `configs/`,
   results, notebooks and the top-level `docs/`, `packages/` wait for content. `runs/` is created with the first record
   (no `.gitkeep`).
4. **Every Experiment and library has its own `pyproject.toml`, locked differently.** Libraries are workspace members
   sharing the root lock, so one dev environment tests them all; they change only in preparation, so the shared lock is
   never edited in parallel. Experiments stay out of the workspace with their own `uv.lock` and path dependencies, so
   parallel experiments never touch one lock and may need conflicting versions. Consequence: a library tested in the
   workspace may run under other versions inside an Experiment; the Experiment's own tests and trial runs confirm it.
5. **Tests sit next to what they test.** No root `tests/`: harness tests in `scripts/tests/`, library tests under
   `packages/<name>/`, Experiment tests in the Experiment. A root `tests/` suggests a product; there is none.
6. **Tests pin behaviour, not coverage.** Write one when it makes people and agents surer of the code; no coverage
   target.
7. **Dependencies point one way.** Experiments import from `packages/`; `packages/` never imports from experiments.
   Libraries stay fine-grained to avoid interfaces that need breaking changes.

Large data, checkpoints and telemetry stay outside Git as long as a run record or README gives a stable reference.

## Naming

| Object            | Format              | Rule                                                                                                                                               |
| ----------------- | ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Experiment        | `exp-NNN-<slug>`    | NNN = experiment issue number, zero-padded to 3; slug = 2-4 lowercase words joined by `-`; same string for `specs/`, `experiments/` and the branch |
| Run               | `R001`, `R002`, …   | increments within the Experiment, counting unmerged run branches; retries take a new number                                                        |
| Task              | `T001`, `T002`, …   | in `specs/<id>/tasks.md`; numbers never reused                                                                                                     |
| Experiment branch | `exp-NNN-<slug>`    | the Experiment ID                                                                                                                                  |
| Run branch        | `run/<exp-id>/R###` | from the Experiment branch, merged back with a merge commit                                                                                        |
| Synthesis branch  | `synthesis/<epic#>` | from the rendezvous commit; PR label `synthesis`, rendezvous hash in the PR body                                                                   |
| Other branches    | `<type>/<slug>`     | harness, library and doc changes prepared by anyone, merged by a human                                                                             |
| Issue reference   | `#23`               | the number inside the Experiment ID; the Epic is the issue's parent on the platform                                                                |

Issue numbers are global in the main repository, so forks never collide and abandoned numbers are never reused; the
costs are gaps in the sequence and that an experiment issue must exist before an Experiment starts.

## Branches

Four requirements; any structure meeting them works:

1. One mainline everyone recognises (`main`): preparation changes land here, the rendezvous is taken here, results end
   here. Protected; shared-part changes are merged by humans.
2. Each Experiment has an isolated line of work (a branch, a branch in a fork, or an agent worktree) touching only its
   own directories.
3. The shared part stands still during experimentation, whatever time each line was branched.
4. Commits referenced by runs are kept as they are: experiments and syntheses enter `main` with full ancestry, no
   squash, no rebase. Experiment and synthesis PRs use the merge-commit method.

| Structure                                | How                                                                                                                  | Fits                                                      | Cost                                                                                    |
| ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| mainline + experiment branches (current) | each Experiment branches from `main`, returns with a merge commit                                                    | a small team in one repo, or one person with agents       | `main` moves during experimentation; the freeze rests on protected paths and convention |
| fork workflow                            | each researcher forks, branches in the fork, opens PRs to the main repo; everyone syncs at preparation               | several researchers, or contributors without write access | Epics and experiment issues exist only in the main repo                                 |
| one integration branch per Epic          | branch at the end of preparation; experiments branch from and return to it; merged to `main` at the next preparation | a visible branch point for the frozen environment         | one more layer, alive for a whole round                                                 |

Committing straight to `main` is excluded: every Experiment needs a PR, because the approval label and the merge review
hang on it. Worktrees for parallel agents are extra local lines inside any structure. Release-oriented branch models
have no use here. No long-lived branch besides `main`.

**Append-only discipline.** Once an Experiment has its first Formal Run, its branch is never rebased, amended or
force-pushed; updates from `main` come in by merge. Run branches merge back with `--no-ff` (`evidence.md`).

## Commit messages

Format `<scope>: <summary>`, ASCII only, title at most 50 characters, summary imperative and lowercase, no trailing
period; an optional body after a blank line wrapped at 72. Scope is the directory or concern touched
(`scripts: reject bare email`, `harness: add tracker recipe`). On an Experiment branch or its run branches the scope is
the short id `exp-NNN`, not the full Experiment ID, so the title fits in 50 characters (`exp-023: add r001 record`,
`exp-023: R001 completed`). No agent attribution of any kind. The commit-msg hook (`scripts/check_commit_message.py`)
enforces the format, rejects agent attribution, allows human `Co-Authored-By` only with noreply addresses, and rejects a
non-noreply author identity. Set `git config user.email` to the platform noreply address before the first commit.

## Language

English for code, comments, commit messages, issues, PRs, and every agent-facing file (`AGENTS.md`, knowledge, skills,
Spec Kit commands and templates, specs, run records, READMEs). `README.md` is the authoritative human-facing document;
`README.zh.md` mirrors it in Chinese and is updated whenever `README.md` changes.
