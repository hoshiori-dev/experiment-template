# Research loop

Read this before starting, iterating, finishing or closing out an Experiment, before a Formal Run, and before
synthesizing an Epic. Source of truth for how work flows; `governance.md` says who decides, `evidence.md` says what a
Formal Run must leave behind.

## The five objects

| Object     | What it is                                                                | Where it lives                                                         |
| ---------- | ------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| Epic       | One round of research; direction approved and published by a human        | A GitHub issue with label `epic`, nowhere else                         |
| Experiment | One concrete goal and the set of runs made for it                         | A sub-issue (label `experiment`) + `specs/<id>/` + `experiments/<id>/` |
| Formal Run | One research decision plus one reproducible launch that yields evidence   | `experiments/<id>/runs/R###.yaml`                                      |
| Rendezvous | A commit on `main` where parallel experiments are collected for synthesis | A commit hash only; written in no file                                 |
| Synthesis  | Proposed changes to accepted knowledge, derived from the rendezvous       | A pull request changing `docs/`, label `synthesis`                     |

The first three nest: an Epic holds Experiments, an Experiment holds runs. An Experiment is a goal, not a single launch:
preprocessing, a sweep and training may each run many times under one Experiment. Only the runs declared as Formal Runs
count as evidence; one Formal Run maps to one or more tracker trials.

## One round

Direction Gate (human publishes the Epic) → Experiments run in parallel → Rendezvous (one commit fixed) → Synthesis
(agent proposes knowledge changes) → Acceptance Gate (human merges). Open questions from the synthesis feed the next
Epic.

| You want to            | The agent                                                                          | Last step belongs to    |
| ---------------------- | ---------------------------------------------------------------------------------- | ----------------------- |
| open a round           | drafts the Epic (`speckit.research.epic`)                                          | human publishes         |
| plan the round         | proposes the Experiments and creates their issues (`speckit.research.experiments`) | agent (high-automation) |
| study a question       | starts an Experiment from an experiment issue                                      | governance model        |
| make progress          | iterates the Experiment                                                            | agent                   |
| produce evidence       | executes a Formal Run (`speckit.research.run`)                                     | agent                   |
| close a question       | finishes the Experiment (`speckit.research.finish`)                                | governance model        |
| close a round          | synthesizes the Epic (`speckit.research.synthesize`)                               | human merges            |
| see where things stand | shows research status (`just status`, read-only)                                   | nobody                  |

"Governance model" means human-led or high-automation; see `governance.md`.

## Two phases

| Phase        | Preparation                                                          | Experimentation                                              |
| ------------ | -------------------------------------------------------------------- | ------------------------------------------------------------ |
| Job          | digest the last round, plan the next, improve the shared environment | run experiments inside that environment, collect evidence    |
| May change   | shared part: `docs/`, `packages/`, the harness, the next Epic's plan | only `specs/<id>/` and `experiments/<id>/`                   |
| Leaves alone | finished Experiments                                                 | the shared part                                              |
| How          | everyone together, versions brought into line                        | each person or agent in its own workspace, committing freely |
| Ends when    | a human publishes the next Epic                                      | every Experiment is done                                     |

"Environment" here is the broad one everyone faces when experiments start: knowledge, constraints, shared libraries,
tools and rules. A Formal Run's execution environment is a different thing (`evidence.md`).

Shared libraries are born in preparation: logic that must stay identical across experiments and is already agreed on or
reused is extracted into `packages/`. During experimentation, logic an Experiment needs lives in its own directory.

A defect in the shared part found during experimentation is worked around locally: copy the needed logic into the
Experiment and adapt it, or take another route; record what was bypassed and why in the README and the PR, and leave the
fix for the next preparation phase. The checks that constrain the agent are the exception: a failing check is fixed at
its cause, never bypassed. What cannot be worked around stops this one Experiment (`governance.md`).

Finished Experiments are frozen. A later environment change is no reason to edit their code.

## Leaving the loop

The loop does not end by itself. At every preparation phase the human researcher and the agent judge together whether
the evidence supports the project's intended conclusion; the human must take part. Not enough: plan the next Epic.
Enough: leave for reporting and publishing (`reports/`, code release). Gaps found while writing are filled with
Experiments that again have an Epic, a spec and Formal Runs.

## Epic

Published when a maintainer adds `epic:approved`. The body carries five fields:

| Field         | Content                                                                                                       |
| ------------- | ------------------------------------------------------------------------------------------------------------- |
| Objective     | what this round must settle and why now                                                                       |
| Scope         | which Experiments belong, which explicitly do not                                                             |
| Constraints   | data, models, protocols and comparisons every Experiment follows, including allowed data sources and licences |
| Budget policy | unit, total cap for the Epic, allowance per Experiment; "unlimited" is written out, never left blank          |
| Exit criteria | when synthesis may start; required (without it the agent cannot tell when to stop opening Experiments)        |

Experiment issues are sub-issues of the Epic (`gh issue view <n> --json parent` reads the link). Each carries the
allowance planned for it; the binding cap is the one in its spec and may not exceed that allowance.

An agent may draft an Epic; only a human publishes it. Numbers the human did not give stay blank for the human to fill.
Before handing over, the drafting agent checks completeness: budget policy present, scope decisive enough to classify an
Experiment, data sources and licences named, exit criteria present when high-automation. Gaps found during
experimentation can only stop the agent to wait for a human, so they are found now.

**Validity** is checked with `just epic-status <n>` (never by eye). All four must hold: the issue is open; it carries
`epic:approved`; the label was added after creation, not at creation; the body was not edited after labeling. Exit code
1 means invalid: stop the loop. Exit code 2 means unreachable after retries: stop as well; validity is never assumed.
The agent never edits, closes or reopens an Epic; remarks go into comments.

## Experiment

**Identity.** `exp-NNN-<slug>`: the experiment issue number zero-padded to three digits plus two to four lowercase
words. The same string names `specs/<id>/`, `experiments/<id>/` and the branch. Experiments are not nested under Epics;
the parent is read from the platform.

**Three files, three binding forces** (`specs/<id>/`):

| File       | Nature      | Rule                                                                                     |
| ---------- | ----------- | ---------------------------------------------------------------------------------------- |
| `spec.md`  | normative   | what, why, constraints, stop conditions, budget. Any change invalidates the approval     |
| `plan.md`  | advisory    | the current strategy; rewritten when evidence changes it, not a history                  |
| `tasks.md` | operational | rolling ledger; unstarted tasks come and go freely, done or dropped ones are only marked |

Test for spec membership: if violating the sentence would disqualify the Experiment even with a good result, it is spec;
otherwise plan. "Both arms use the same training images" is spec; "try six learning rates first" is plan.

**Lifecycle.** Fence first: confirm the Epic is valid, create the branch `<id>` and its PR, write the spec. Approval
(`governance.md`). Then free exploration: what to try, how to build, how to run is the agent's choice; the record is the
commit history, run branches, run records, plan and ledger. Hand-over: README, code, the Formal Runs that support the
conclusion; provenance verified; merged. A spec changed after approval goes back to approval before any Formal Run: the
party that changed it removes the `spec:approved` label and asks for a new approval (`governance.md`, Spec approval,
says who does that under each setting). Budget exhausted, or the goal unreachable under current conditions: stop this
Experiment and tell the human. Epic no longer valid: stop the loop, which means no new run and no new Experiment starts
while runs already running finish and are recorded.

**Close-out and the deletion test.** Close-out does not require every task done. It requires that if `specs/<id>/` were
deleted, `experiments/<id>/README.md` alone still tells what was studied, what was run, where the evidence is, the
conclusion, the limits, and how to reproduce. Hence six fixed sections: `Question`, `What was run`, `Evidence`,
`Conclusion`, `Limits and remaining uncertainty`, `Reproduce`. The status line takes one of `in progress`, `answered`,
`answer is negative`, `inconclusive`. Negative and inconclusive results are legitimate outputs. A failed or aborted run
is not "informative" unless the README says exactly what it showed. Also at close-out: every conclusion names its
supporting Formal Run; claims resting on informal runs are deleted or rewritten; no run branch is left unmerged;
unfinished tasks are marked dropped with a reason or kept as planned with the follow-up named in the README; provenance
is verified (`evidence.md`); actual usage is written back to the experiment issue; the branch is merged into `main` with
a merge commit.

## Formal versus informal runs

|               | Informal run                      | Formal Run                                                   |
| ------------- | --------------------------------- | ------------------------------------------------------------ |
| Purpose       | debug, smoke, explore, size a run | produce evidence                                             |
| Process cost  | none, any time                    | approved spec, run record, frozen environment, source commit |
| Code source   | the working tree                  | committed content only                                       |
| Leaves behind | nothing traceable                 | run record, frozen manifest, commits, tracker record         |
| Proof value   | none                              | evidence                                                     |

An observation from an informal run becomes evidence only after a Formal Run reproduces it. Informal runs can leak
held-out metrics into design decisions; the spec's `holdout` field says how that is prevented and the approver checks it
exists (the ML habit: commit the design, split, grid and decision rule before any informal run that evaluates held-out
data; report later design changes as deviations under Limits). A run's terminal state describes execution only
(`completed`, `failed`, `aborted`); whether the result is good belongs in the README.

## Rendezvous and synthesis

Synthesis is the first act of preparation. Fix the rendezvous: a commit on `main`, usually the current tip, confirmed
with the human. Branch `synthesis/<epic-number>` from it; merge nothing newer and cherry-pick nothing while reasoning,
or the evidence base becomes unclear. Choose evidence explicitly: what is included, what excluded, why. Write proposed
knowledge into `docs/` in its style: dense, stable terms; what is accepted and which evidence supports it, linked to
Experiment READMEs; only qualifiers that change how the knowledge is used; no run logs, no Epic history, no index;
overturned claims are edited or removed. Open the PR with label `synthesis`, the rendezvous hash, the evidence choices
and the open questions in its body, then stop: merging is the Acceptance Gate. At the rendezvous also run the
`harness-checkup` skill; its report stays separate from the synthesis branch.

## Where artifacts go

| Artifact   | Holds                                    | Relation to evidence                                                       |
| ---------- | ---------------------------------------- | -------------------------------------------------------------------------- |
| `docs/`    | accepted knowledge                       | enters only through an accepted synthesis                                  |
| `reports/` | deliverables for people: papers, reports | written from `docs/`; gaps found while writing may open a new Epic         |
| `demos/`   | capability demonstrations                | never evidence; a phenomenon seen in a demo needs an Experiment to confirm |
| release    | a separate project                       | may copy or rewrite research code; never depends on `packages/`            |
