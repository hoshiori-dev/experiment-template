# experiment-template

A template for research projects where humans set the direction and accept the conclusions, and agents do the work in
between. Two things have to hold for every result: it can be reproduced, and someone who was not there can understand
it.

The design uses a machine-learning project as its worked example, but the rules are about boundaries, not methods.
Wherever this README mentions containers, lock files or GPUs, that is the machine-learning example; the rule behind it
applies to any kind of experiment.

A Chinese translation lives in [README.zh.md](README.zh.md). This file is the authoritative one.

## The whole design on one page

**Three stages.** A project starts by setting up the repository and its harness. It then cycles between a preparation
stage and an experiment stage, as many rounds as it takes to collect enough evidence. At some preparation stage the
researchers and the agent agree that the evidence is sufficient, and the project leaves the loop to write the report and
publish code. A human takes part in that decision; gaps found while writing send the project back for more experiments.

**Preparation and experiment alternate.** Preparation changes only the shared parts: accepted knowledge in `docs/`,
shared libraries in `packages/`, and the harness. Experiments change only their own directories. During the experiment
stage the shared parts are frozen, so people and agents work in parallel without merge conflicts; once an experiment is
finished, it is frozen too.

**Epic, Experiment, Formal Run.** An Epic is one round of research: a GitHub issue a maintainer publishes by adding the
`epic:approved` label. It names the objective, scope, constraints and budget policy. Each Experiment is a sub-issue of
the Epic with one concrete goal; its ID (`exp-023-normalization-instability`) names its spec directory, its experiment
directory and its branch. A Formal Run is one research decision plus one reproducible launch, recorded in
`experiments/<id>/runs/R001.yaml`. Only Formal Runs count as evidence. Debug and smoke runs are free, and prove nothing.

**Two gates belong to humans.** A human publishes each Epic (the direction gate) and merges each synthesis pull request
into `docs/` (the acceptance gate). In the high-automation model shipped here, the agent plans the experiments under an
Epic, an independent agent with a clean context approves each spec, and the agent merges experiment pull requests that
touch only their own directories.

**Budget is machine-checked.** Every experiment's spec carries a limit. Each run reserves before it starts and records
actual usage when it ends, failed runs included, and the sum must stay under the limit. When the budget runs out, the
agent stops and tells a human; only a human raises a budget.

**Protected paths.** The agent cannot loosen what constrains it. Rules, checks, permissions, `docs/` and `packages/` can
be edited on a branch, but only a human merges them. The last line is branch protection on the hosting platform, which
the owner configures by hand.

**A fenced workspace.** The harness gives each experiment a workspace, fences it with direction, scope, budget and
evidence requirements, and passes the tools in. How the agent explores, builds and runs inside the fence is its own
choice. What comes back out is a README, code and the Formal Runs that support the conclusion.

**One source of truth.** There is no status database. Whatever can be derived from Git, run records and the tracker is
never stored a second time.

## What ships

| Setting                         | Shipped value                                                                                                                       |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Governance model                | high-automation: the agent plans the experiments under an Epic, writes specs, an independent agent approves, agent merges           |
| External writes                 | on: the agent pushes its branches, opens issues and pull requests, comments and labels; never pushes `main` or force-pushes         |
| Budget                          | on: experiment-level limit in the spec front matter, checked offline by `scripts/budget.py`                                         |
| Epic-level hard cap             | not machine-enforced; the approver adds up the Epic's experiments                                                                   |
| Approval record                 | label `spec:approved` on the experiment's pull request, read with `gh`                                                              |
| Epic validity                   | issue open, `epic:approved` added after creation, body unedited since                                                               |
| Publishing safety               | public-repo standard: gitleaks with extended PII and path rules, plus an agent read-through                                         |
| Agent attribution               | forbidden in commits, issues, PRs and comments; Claude Code's credit lines are switched off; human co-authors use noreply addresses |
| Commit address                  | platform noreply only                                                                                                               |
| Execution environment (example) | local Docker, CPU or exactly one GPU, no network                                                                                    |
| Tracker (example)               | Trackio with local storage under `.local/trackio/`                                                                                  |
| Platform                        | GitHub; `gh` for queries and the writes above                                                                                       |
| Branches                        | `main`, one branch per experiment (`exp-NNN-slug`), run branches `run/<exp-id>/R###`, `synthesis/<epic#>`, `<type>/<slug>`          |
| Example experiment              | none; `template/experiment/` is the starter                                                                                         |

## Quick start

1. Create a repository from this template.
2. Open it in the devcontainer, or run `uv sync && pre-commit install --install-hooks` locally. The devcontainer runs
   both for you. The research commands are already installed into Spec Kit; `just speckit-install` is needed only after
   editing `speckit/` ([speckit/README.md](speckit/README.md)).
3. Configure GitHub by hand; nothing in the repository can do this for you:
   - create the labels in `.github/labels.yml`, either by running the labels workflow or with `gh label create`;
   - decide who owns the protected paths in `.github/CODEOWNERS`.
4. Before the first Epic, configure the platform for an agent that writes. Without this, "protected paths are merged
   only by humans" is a convention with nothing enforcing it:
   - a branch protection rule or ruleset on `main`: require a pull request and review from code owners, and allow merge
     commits only (run history must survive). Repository admins keep bypass, so you can merge harness pull requests
     yourself; who merged is the audit signal;
   - a credential for the agent without admin rights: a machine account with the write role, or a fine-grained token
     with `Contents: write` (push and merge), `Pull requests: write` and `Issues: write` and nothing else. Whether a
     fine-grained token of your own admin account inherits the bypass is not verified; a machine account avoids the
     question;
   - the approving agent shares that credential, so the platform cannot tell who applied `spec:approved`: the
     independence of the approval is procedural. Give the approver its own account or token if you need the platform to
     record it.
5. Open your agent and draft the first Epic with `/speckit-research-epic`. The agent writes the draft; you publish the
   issue and add `epic:approved`.

From then on, say what you want and the agent runs the matching command.

## Daily commands

The commands are Spec Kit skills installed for Claude Code; Codex reaches them through symlinks in `.agents/skills/` and
OpenCode reads `.claude/skills/` directly, so the names are the same in all three.

| You want to                   | Ask the agent to                                                    | Command                                                 | Last step by                                   |
| ----------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------- | ---------------------------------------------- |
| Start a round of research     | Draft the Epic                                                      | `/speckit-research-epic`                                | you: publish the issue and add `epic:approved` |
| Plan the round                | Propose the Experiments of a published Epic and create their issues | `/speckit-research-experiments`                         | the agent                                      |
| Research a question           | Start an Experiment from an experiment issue                        | `/speckit-specify`                                      | the agent: push, open the PR, ask for approval |
| Check a spec against its Epic | Review the spec                                                     | `/speckit-research-approve`                             | a clean-context agent: add `spec:approved`     |
| Keep going                    | Iterate on the Experiment                                           | `/speckit-plan`, `/speckit-tasks`, `/speckit-implement` | the agent                                      |
| Produce evidence              | Execute a Formal Run                                                | `/speckit-research-run`                                 | the agent                                      |
| Finish a question             | Wrap up the Experiment                                              | `/speckit-research-finish`                              | the agent: merge, if only its own directories  |
| Close a round                 | Synthesize the Epic                                                 | `/speckit-research-synthesize`                          | you: merge the synthesis pull request          |
| See where things stand        | Show research status (read-only)                                    | `/speckit-research-status`                              | nobody                                         |

The last column reflects the high-automation model. In the human-led model the spec approval and the experiment merge
move back to you.

Behind the commands sit plain tools you can run yourself: `just check`, `just status`, `just budget <exp>`,
`just preflight <exp> <run>`, `just epic-status <n>`, `just scan`. Run `just --list` for all recipes.

## Repository layout

```text
.
│   files for agents
├── AGENTS.md                  entry point: the map an agent reads before working
├── CLAUDE.md                  one framework's entry; only includes AGENTS.md
├── .agents/
│   ├── knowledge/             harness knowledge: rules, constraints, how things work
│   └── skills/                procedures: step-by-step operations
├── .claude/                   Claude Code settings and permissions
├── .codex/                    Codex settings and permissions
├── opencode.json              OpenCode settings and permissions
├── speckit/                   source of the research preset and extension
├── .specify/                  Spec Kit working directory, committed
│
│   tools and checks
├── justfile                   one recipe per action
├── scripts/                   check scripts
│   └── tests/                 tests for the scripts and harness files
├── .pre-commit-config.yaml    hooks at commit, commit-msg and push
├── .gitleaks.toml             scanner rules
├── pyproject.toml             root workspace: management tools and shared libraries
├── uv.lock                    root lock file; runs never install from it
├── .devcontainer/             development container with the tools above
├── .github/                   issue and PR templates, labels, CI
├── template/                  starter for a new experiment
│
│   shared content (empty, held by .gitkeep, until there is something to put in them)
├── packages/<name>/           a shared library with its own pyproject and tests
├── docs/                      accepted experimental knowledge
│
│   experiments
├── specs/<id>/                spec, plan and tasks of one Experiment
├── experiments/<id>/          README, code, own pyproject, tests
│   └── runs/                  run records and frozen requirement files
│
│   deliverables (empty until report time)
├── reports/                   papers and reports
├── demos/                     demonstrations, never evidence
│
│   local only, ignored by Git
└── .local/                    data, run outputs, tracker storage, drafts
```

Everything above `specs/` is the shared part; humans merge changes to it during preparation. `specs/<id>/` and
`experiments/<id>/` are the only paths an experiment touches.

## Adapting the template

Every setting in the table above is the owner's decision. The agent can lay out the options and their cost, but it
cannot change them to widen its own reach. [.agents/knowledge/adaptation.md](.agents/knowledge/adaptation.md) walks
through each one: the governance model, the budget and its unit, an Epic-level hard cap, protected paths, agent
attribution, the commit address, approval-label automation, external writes, the publishing-safety standard, and
swapping the execution environment, the tracker or the platform.

Two gates cannot be adapted away: a human publishes every Epic, and a human merges every synthesis.

## Not implemented or untested

- No example experiment ships. Results cannot be fabricated, and a real one would need real compute;
  `template/experiment/` is the starting point.
- Nothing has been run end to end: no Epic, Experiment or Formal Run has gone through the loop in either governance
  model.
- The independent approving agent is a clean-context sub-agent by procedure: the command asks for one, and nothing
  checks that the approver is not the author. A separate account for it is the owner's choice (quick start, step 4).
- Other execution environments, other trackers and GitLab have adaptation notes only; none of them has been run.
- The Epic-level budget cap is checked by the approver, not by a script.
- Approval-label automation (removing `spec:approved` when the spec changes, checking who added it) is documented but
  not enabled.

## License

[Apache License 2.0](LICENSE).
