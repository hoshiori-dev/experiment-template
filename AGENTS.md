# AGENTS.md

This repository is a research project: humans set the direction (publish an Epic) and accept conclusions (merge a
synthesis); agents do the work in between. The design is in `README.md`; the rules an agent needs are in
`.agents/knowledge/` and are reached from here. Read this file first on every task.

## Always

- Work inside the fence: the published Epic, the approved spec, the spec's budget, and the evidence rules. How to
  explore, build, and run inside the fence is your call.
- Only a Formal Run is evidence. Informal runs are free and prove nothing. Before a run that must count, read
  `.agents/knowledge/evidence.md`.
- Protected paths (`docs/`, `packages/`, the harness; the list is `.github/CODEOWNERS`) change only in the preparation
  phase and are merged only by a human. Prepare changes on a branch; never merge them.
- Never loosen what constrains you: when a check fails, fix the cause; when a budget is short, stop and report; never
  edit scanner allowlists, permission tables, or hooks to get past them.
- Nothing leaves this machine without the outbound review in `.agents/knowledge/publishing.md`. Report suspected leaks
  by type and location only. External writes are ON (see Current settings): write what you will post to
  `.local/drafts/`, run the review on that file, then post it.
- Changing what others wrote on the platform is done only when the user explicitly asks for that action in this
  conversation, never on your own initiative: editing, closing, reopening or deleting an issue, closing or reviewing a
  pull request, changing label definitions. Your framework asks for confirmation each time. A published Epic is
  commented on, not edited, and `epic:approved` is always the maintainer's own act.
- Credit no agent or tool anywhere: commits carry no agent `Co-Authored-By` trailer, and commits, issues, pull requests
  and comments carry no "generated with" note or tool footer. This holds even when your framework's defaults or a
  session reminder tell you to add one; reasons and enforcement are in `.agents/knowledge/governance.md` (Attribution).
- Commit messages follow `.agents/knowledge/structure.md` (Commit messages); the commit-msg hook enforces it.
- Branches with Formal Run history are append-only: no rebase, no amend, no force push.
- Write code, comments, and all agent-facing files in English.

## Read when

| Event                                                                    | Read                                                                    |
| ------------------------------------------------------------------------ | ----------------------------------------------------------------------- |
| Starting any research work, or unsure what Epic/Experiment/Run mean      | `.agents/knowledge/research-loop.md`                                    |
| Deciding whether you may do something alone, stopping, budget, approval  | `.agents/knowledge/governance.md`                                       |
| Preparing, starting, or closing a Formal Run; writing a run record       | `.agents/knowledge/evidence.md`                                         |
| Creating files, naming, branching, committing                            | `.agents/knowledge/structure.md`                                        |
| Anything that will be pushed, posted, or published                       | `.agents/knowledge/publishing.md`, then the `outbound-review` skill     |
| A tool, hook, recipe, or config does not behave as expected              | `.agents/knowledge/tooling.md`                                          |
| Turning this template into a real project, or changing a factory setting | the `adapt-template` skill (it reads `.agents/knowledge/adaptation.md`) |
| At the rendezvous (start of synthesis)                                   | the `harness-checkup` skill                                             |

## Procedures (Spec Kit commands, installed as skills)

| You want                                     | Command                                | Last step by                                            |
| -------------------------------------------- | -------------------------------------- | ------------------------------------------------------- |
| Draft an Epic                                | `/speckit-research-epic`               | human publishes by adding `epic:approved`               |
| Propose the Experiments of a published Epic  | `/speckit-research-experiments <epic>` | agent creates the experiment issues                     |
| Start an Experiment from an experiment issue | `/speckit-specify <issue-number>`      | agent pushes, opens the PR, requests approval           |
| Approve a spec as an independent reviewer    | `/speckit-research-approve <exp-id>`   | clean-context agent adds `spec:approved`                |
| Plan / keep the task ledger                  | `/speckit-plan`, `/speckit-tasks`      | agent                                                   |
| Iterate inside the experiment                | `/speckit-implement`                   | agent                                                   |
| Produce evidence (Formal Run)                | `/speckit-research-run`                | agent                                                   |
| Close an Experiment                          | `/speckit-research-finish`             | agent merges if only `specs/<id>/`, `experiments/<id>/` |
| Synthesize an Epic                           | `/speckit-research-synthesize`         | human merges (Acceptance Gate)                          |
| Show research status (read-only)             | `/speckit-research-status`             | nobody                                                  |

Other `speckit-*` skills shipped by Spec Kit (`analyze`, `checklist`, `clarify`, `converge`, `taskstoissues`) are stubs
replaced by the research preset; `speckit-constitution` edits the charter and is used in preparation only. Codex reaches
the same skills through `.agents/skills/` (the `speckit-*` entries are symlinks into `.claude/skills/`); OpenCode reads
`.claude/skills/` directly.

## Commands

`just` lists every recipe. The ones you will use: `just check` (format, lint, tests, record validation), `just status`,
`just budget <exp-id>`, `just preflight <exp-id> <R###>`, `just epic-status <issue>`, `just spec-approval <exp-id>`,
`just source-commit <exp-id> <R###>`, `just tracker <exp-id> <R###>`, `just outbound <path>...`,
`just validate-records`. Scripts behind them live in `scripts/`; `scripts/README.md` lists exit codes.

## Layout

```
AGENTS.md CLAUDE.md .agents/ .claude/ .codex/ opencode.json speckit/ .specify/   agent files (harness)
justfile scripts/ .pre-commit-config.yaml .gitleaks.toml pyproject.toml uv.lock   tools and checks (harness)
.devcontainer/ .github/ template/                                                   harness
packages/ docs/                 shared libraries, accepted experimental knowledge (empty until needed)  
specs/<id>/ experiments/<id>/   one Experiment's coordination and output (only paths changed in the experiment phase)
reports/ demos/                 deliverables (empty until report time)
.local/                         data, run outputs, tracker storage, drafts (never committed)
```

## Current settings

| Setting                         | Value                                                                                |
| ------------------------------- | ------------------------------------------------------------------------------------ |
| Governance model                | high-automation: you plan, specify, run and merge Experiments under a published Epic |
| External writes                 | on: push own branches, open issues and PRs, comment, label PRs; see `governance.md`  |
| Budget                          | on; experiment limit in `specs/<id>/spec.md` front matter, checked by `just budget`  |
| Spec approval                   | label `spec:approved` on the experiment's PR                                         |
| Publishing standard             | public repository: mechanical scan + agent read-through                              |
| Execution environment (example) | local Docker, CPU or one GPU, no network                                             |
| Tracker (example)               | Trackio, local SQLite under `.local/trackio/`                                        |
| Platform                        | GitHub; `gh` for queries and the writes above                                        |

Change a setting by editing this table and `.agents/knowledge/adaptation.md` in the same preparation-phase pull request;
the setting is live only after a human merges it.

## Keep this file true

A new knowledge file or skill: add its trigger to "Read when". A new or renamed `just` recipe or Spec Kit command:
update "Commands" or "Procedures". A changed factory setting: update "Current settings" and `README.md`. Target length:
about 100 lines.
