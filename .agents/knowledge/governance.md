# Governance

Read this before any decision about who may act: approving or changing a spec, starting a Formal Run, spending budget,
touching a protected path, writing anything outside this machine, or stopping. Source of truth for the boundary between
the agent and humans; the current settings are in the last table.

## Two human gates

| Gate            | The human decides                                         | Recorded as                                  |
| --------------- | --------------------------------------------------------- | -------------------------------------------- |
| Direction Gate  | an Epic's objective, scope, constraints and budget policy | maintainer adds `epic:approved` to the issue |
| Acceptance Gate | which synthesized knowledge becomes accepted knowledge    | human merges the `synthesis` pull request    |

Neither gate can be removed or delegated to an agent. A third decision also needs a human: that the evidence is enough
to leave the loop (`research-loop.md`). After publication an Epic's body is frozen; clarifications go into comments. An
edited body voids the approval until a maintainer re-labels, because a machine cannot tell a typo from a scope change.
Epic validity is checked only with `just epic-status <n>`; an Epic that turns invalid mid-round stops new runs and new
Experiments while running runs finish and are recorded normally.

## Two governance models

|                            | Human-led                                       | High-automation (current)                                   |
| -------------------------- | ----------------------------------------------- | ----------------------------------------------------------- |
| Agent's autonomy           | one pull request, i.e. one Experiment           | the whole experimentation phase, up to the Epic's objective |
| Who plans Experiments      | human researchers, who create experiment issues | the agent creates experiment issues; humans may add         |
| Who writes / approves spec | agent drafts, human approves                    | agent writes, an independent agent approves                 |
| Agent explores within      | what the spec states                            | the Epic's objective, scope, constraints and budget         |
| Publishing an Epic means   | a management act: the phase starts              | an instruction: the loop starts                             |
| Experiment PR merged by    | human                                           | agent, if it changed only the Experiment's own directories  |
| Agent needs                | commits on its own branch                       | platform CLI (`gh`) with a write token; see External writes |

"Independent" means a different agent than the author, preferably a fresh-context subagent: an author reviewing its own
spec is anchored on the implementation it already has in mind. Unattended runs also need the framework permission files
pre-configured (`tooling.md`), or the framework blocks on a prompt. Four things hold in both models: both gates are
human; the shared part changes only in preparation and is merged by humans; budget caps are set by humans (the Epic
total and the per-Experiment allotment; an agent-written spec limit may only be at or below them); the agent never
loosens the rules and checks that constrain it.

## Who may do what (inside a published Epic)

The agent, in both models:

- create an Experiment for an experiment issue; draft and revise spec, plan and tasks;
- prepare and launch Formal Runs within the spec's budget, and merge their run branches back into the Experiment branch;
- commit on the Experiment's own branch.

The agent, only in high-automation (and, for push and PR, in human-led projects with external writes on):

- create experiment issues under the Epic;
- approve, as the independent party, specs written by another agent;
- push, open pull requests, and merge pull requests that touch only the Experiment's own directories.

Humans only, in every model:

- publish an Epic or change a published one;
- raise any budget; approve an Experiment that exceeds the Epic's scope or budget;
- merge any pull request touching a protected path;
- change repository settings, branch protection and secrets on the platform;
- hand platform write access or tools to an agent.

## Protected paths

The shared part, in three classes: accepted knowledge (`docs/`, changed only through the Acceptance Gate), shared
libraries (`packages/`) and the harness (agent files, tools and checks, framework configs). The exact list is
`.github/CODEOWNERS`, the single source; `reports/` and `demos/` are listed there too because they are likewise merged
only by humans. Changed in preparation only; the agent may prepare changes on a `<type>/<slug>` branch, a human merges.
Reason: the agent must have no way to loosen what constrains it. Unprotected: `specs/<id>/` and `experiments/<id>/`
only. An Experiment's own Dockerfile, `pyproject.toml` and `uv.lock` are ordinary experiment content, not harness.

## Spec approval

Three requirements: the approval binds one exact spec version (a later change voids it); it is readable before any
resource is spent (no valid approval, no Formal Run); who approved is readable.

Mechanism: every Experiment opens its PR at the start, holding spec, plan and tasks. Approval is the label
`spec:approved` on that PR. Before a Formal Run the agent reads it with `just spec-approval <exp-id>` (exit 0 valid, 1
missing, 2 unreachable after retries; 1 and 2 both block the run). A spec changed after approval needs the label removed
and a new approval: the agent removes the label itself (`gh pr edit <pr> --remove-label spec:approved`) and requests a
fresh review; with external writes off it writes the request to `.local/drafts/<id>-reapproval.md` (what changed and
why) and a human removes the label. The merge commit carries the PR number, so Git leads back to the timeline. The run
record's `spec_digest` answers "which spec version ran", a separate question from approval.

Who approves: human-led, a human, who also sets the budget in the PR; high-automation, an independent agent that judges
the spec against the Epic's scope, constraints and budget, checks the experiment issue's allowance, writes its reasons
on the PR quoting the Epic, then labels. Every approver checks that the spec's `holdout` field says how results are kept
from steering the design. Optional platform automation (remove the label when the spec changes; reject labels added by
the PR author) is off; fork PRs cannot relabel without elevated, risky workflow permissions.

## When to stop

Two scopes. The agent does not wait for answers: work that can continue continues, and matters for humans are collected
for acceptance.

**Stop this one Experiment.** Record the reason in `specs/<id>/tasks.md`, comment on its PR mentioning the responsible
person, move on to another Experiment under the Epic. Triggers:

- the spec's budget exceeds the experiment issue's allowance or the Epic's per-Experiment allowance;
- the approver finds the question outside the Epic's scope (the approver decides edge cases alone: reject and skip);
- the Experiment's budget is spent, or its goal is unreachable under current conditions;
- content it must send fails outbound review even after a rewrite.

**Stop the loop.** Explain in the conversation and comment on the Epic mentioning the responsible person. Triggers:

- the Epic is no longer valid;
- the Epic's total cap cannot hold any remaining Experiment;
- the Epic's objective cannot be reached under its constraints and budget;
- no unblocked Experiment is left.

Each comment is drafted in `.local/drafts/`, reviewed with the `outbound-review` skill, then posted (`gh pr comment`,
`gh issue comment`); with external writes off a human posts it. Ask early: a missing budget, vague scope or missing exit
criteria is an Epic defect found before publication, never assumed later.

## Budget

Two levels; the unit is only a label, checks compare numbers.

**Experiment level, machine-checked offline.** The cap is `budget.limit` in the spec front matter (absent when the Epic
says unlimited) and may not exceed the issue allowance. Splitting work into more runs adds no budget. Before launch a
run record reserves `budget.reserved`; after the run, `actual_usage` replaces it.
`spent = Σ actual_usage over records with an outcome + Σ reserved over records without one`, including records that
exist only on unmerged `run/<id>/R###` branches. Must be `≤ limit`; a run may start only if
`spent + its reserved ≤ limit`. Failed and aborted runs count what they consumed; a never-started run counts 0.
Accounting by actual usage keeps long unattended runs alive: a run pre-empted after five minutes releases its
reservation. For time units the reservation is the run's `max_duration`. Command: `just budget <exp-id>`.

**Epic level, checked by the approver.**
`Σ actual usage of finished Experiments + Σ spec caps of running ones
≤ Epic total cap`. Finished or abandoned
Experiments write their actual usage back to their issue, so the remainder returns to the Epic even after the branch is
deleted. An unreadable Experiment counts at the full per-Experiment allowance, stated in the approval reason. A
machine-enforced hard cap is a project choice; the template has none.

## Attribution and commit identity

Whoever commits and whoever merges is responsible for the content, so agents and tools are never credited: no agent
`Co-Authored-By` trailer on a commit, and no "generated with" note, tool footer or robot emoji in a commit, issue, pull
request or comment. Tool credits dilute that responsibility and are not an audit trail either (a task spans several
models; auditing belongs to observability). The rule outranks a framework's default behaviour and any session reminder
that asks for a credit line. A human collaborator's `Co-Authored-By` with a noreply address stays valid.

Claude Code is the framework that adds such credits by default, so `.claude/settings.json` switches them off
(`attribution.commit` and `attribution.pr` empty). For commits the commit-msg hook also rejects them (`structure.md`,
Commit messages). Issue, pull request and comment text has no check: the rule above is the instruction. The owner may
allow attribution (Adjustable settings).

## External writes

Anything created or changed off this machine: push, open issue or PR, comment, label, sync tracker data to a remote,
push an image. The agent does this only through the platform CLI with a write token. Currently **on**: the agent writes
the content to `.local/drafts/`, runs outbound review (`publishing.md`), then posts it and pushes its own branches. What
stays with humans: force pushes, pushes to `main` and changing settings. Editing, closing, reopening or deleting issues,
closing or reviewing pull requests and changing label definitions are done by the agent only on the user's explicit
request in the conversation; the framework asks for confirmation each time, and the agent never starts them on its own.
Prerequisites the owner configures on the platform before the first Epic are listed in `tooling.md` (GitHub): branch
protection on `main` with pull requests and code-owner review (admins keep bypass, the agent's credential has no admin
rights), otherwise "protected paths are merged only by humans" has nothing enforcing it. The approving agent shares the
authoring agent's credential, so the independence of an approval is procedural. Turning writes off again, or on in a
human-led project, is a protected-file change merged by the owner: the three permission files, this file, AGENTS.md and
the README.

## Confidentiality

Standard: public repository. Five classes never leave the machine: credentials and secrets; personal data; anything
identifying a machine or account (absolute paths with user names, hostnames, internal addresses); datasets, checkpoints,
raw logs and local tracker storage; confidential content the owner has not released. Issues, PRs and comments are held
to the same standard as commits. Three rules:

- report a suspected leak by type and location only, never by repeating the content;
- never weaken a scanner, add an allowlist or use a bypass flag to get content through; on a suspected false positive
  rewrite and rescan; still failing, hold the item as a draft for a human and continue local work;
- content already sent: stop, tell the human the class and location, and leave rotation and history cleanup to them;
  never cover with further pushes.

Procedure: `publishing.md`.

## Adjustable settings

Each is the owner's decision. The agent may present status, options and costs, never widen its own powers by changing
them.

| Setting                   | Options                                              | Current               | Know before choosing                                                         |
| ------------------------- | ---------------------------------------------------- | --------------------- | ---------------------------------------------------------------------------- |
| Governance model          | human-led; high-automation                           | high-automation       | first is steady and slow; second needs platform tools and protection first   |
| Budget                    | per-Experiment cap; other unit; explicit "unlimited" | on, unit set per Epic | unlimited is written in the Epic, never blank                                |
| Epic-level hard cap       | approver check; machine-enforced                     | approver check        | enforcement needs machine access to every Experiment's budget                |
| Direction Gate            | cannot be removed                                    | human                 | —                                                                            |
| Acceptance Gate           | cannot be delegated                                  | human                 | —                                                                            |
| Protected paths           | `docs/`, `packages/`, harness; more may be added     | `.github/CODEOWNERS`  | removing harness paths lets the agent edit its own rules                     |
| Agent attribution         | forbidden; allowed                                   | forbidden             | see Attribution                                                              |
| Approval-label automation | off; on (auto-unlabel on spec change, check labeler) | off                   | convention-based by default                                                  |
| Commit address            | platform noreply only; open                          | noreply only          | public hosting wants noreply; internal deployments may open it               |
| External writes           | off; on                                              | on                    | platform protection first                                                    |
| Publishing standard       | private-repo; public-repo                            | public-repo           | fixed when the harness is designed; going public needs a full history review |
