---
description: Iterate the Experiment - explore freely inside its two directories, keep the ledger, stop at the fence.
argument-hint: "Optional focus for this iteration"
---

## User Input

```text
$ARGUMENTS
```

## Role and goal

You push one approved Experiment toward answering its spec's question. Inside `specs/<id>/` and `experiments/<id>/` you
decide what to try first, how many approaches to try, how to organize code, and how to build and run. Two things hold
throughout: the process stays in the record (commits, ledger, plan, run records; done and abandoned work is marked,
never erased), and any run that is to count as evidence is a Formal Run. Read `.agents/knowledge/evidence.md` before the
first run that should count; read `.agents/knowledge/governance.md` for the stopping rules.

## Steps

1. **Locate and check.** Resolve `<id>` from `SPECIFY_FEATURE_DIRECTORY`, `.specify/feature.json` or the branch name
   (`exp-NNN-*`); confirm `git branch --show-current` is `<id>`. Run `just spec-approval <id>`: exit 0 continues; exit 1
   means the spec has no valid approval and the Experiment waits for the human; exit 2 means the platform is
   unreachable, so informal work may continue but no Formal Run starts. Run `just budget <id>` to know the remaining
   budget. Done when: branch, approval state and remaining budget are known.

2. **Decide the next step.** Read `specs/<id>/spec.md`, `plan.md`, `tasks.md` and `$ARGUMENTS`. Pick the next task, or
   add one (`/speckit-tasks`), and set it `in progress`. Done when: the ledger names what you are doing.

3. **Work.** Edit and commit only under `specs/<id>/` and `experiments/<id>/` (the branch-scope hook rejects other
   paths). Informal runs (debugging, smoke tests, exploration, sizing) need no procedure and leave no traceability; keep
   their output under `.local/`. Respect the spec's held-out protection while exploring: numbers from held-out data seen
   in an informal run never change the design. When a shared library or a check blocks you, work around it inside the
   Experiment's directory and note the workaround in the README; the harness itself is fixed from here. Commit in small
   steps with titles `exp-NNN: <summary>` (the short form of `<id>` as scope keeps titles within 50 characters). Done
   when: the task's outcome is committed and the ledger row moves to `done` or `abandoned (reason)`.

4. **Produce evidence.** When a run must count, run `/speckit-research-run <id>`. Findings from informal runs become
   evidence only once a Formal Run reproduces them. Done when: the run branch is merged back and `just budget <id>`
   still passes.

5. **Repeat** steps 2-4 until a stop condition applies, then go to Stopping.

## Stopping

Stop this Experiment, and only this one, when: the budget is exhausted (`just budget <id>` reports no room for the next
run); or the question is unreachable under the spec's constraints. The completion criteria being met is the good case:
the Experiment is ready for `/speckit-research-finish <id>`.

A spec edited after approval makes the label `spec:approved` stale: no Formal Run starts until the spec is approved
again. In high-automation mode with writes on (the shipped default), remove the label yourself
(`gh pr edit <pr> --remove-label spec:approved`) and request `/speckit-research-approve <id>` from a fresh sub-agent;
informal work may continue meanwhile. With external writes off, `gh pr edit` is denied, so write the request to
`.local/drafts/<id>-reapproval.md` (the PR number, the commits that changed the spec, what changed and why) and ask the
human to remove the label and re-review.

When stopping short, write where to find the reason:

1. a ledger entry in `specs/<id>/tasks.md` (state `abandoned (reason)` or a new `planned` row describing what is left),
2. a comment draft at `.local/drafts/<id>-stop.md` addressed to the person responsible, stating the condition hit, the
   budget spent, and what you recommend; pass it through `just outbound .local/drafts/<id>-stop.md`.

In high-automation mode with writes on (the shipped default), post it with `gh pr comment` and move on to another
Experiment under the Epic. With external writes off, the human posts the comment. An invalid Epic (`just epic-status`)
stops the whole loop: finish running runs, start nothing new, and report to the human.
