---
name: speckit-plan
description: Write or rewrite the advisory plan (current strategy and candidate runs)
  of the current Experiment.
compatibility: Requires spec-kit project structure with .specify/ directory
metadata:
  author: github-spec-kit
  source: preset:research
argument-hint: Optional notes on the strategy to plan
user-invocable: true
disable-model-invocation: false
---

# Speckit Plan Skill

## User Input

```text
$ARGUMENTS
```

## Role and goal

You maintain `specs/<id>/plan.md`, the advisory file of an Experiment. It states the current strategy; it is rewritten
whenever evidence changes the strategy, and its Git history is the record of how thinking moved. Nothing in it binds the
Experiment. The binding text is `spec.md`, and this command never edits that file: a change that belongs in the spec is
reported to the human instead, because any spec edit invalidates approval.

## Steps

1. **Locate the Experiment.** Use `SPECIFY_FEATURE_DIRECTORY` when set, otherwise `feature_directory` from
   `.specify/feature.json`, otherwise the current branch name when it matches `exp-NNN-*` (then also write
   `.specify/feature.json`). When none of these yields a `specs/<id>/` directory, stop and ask which Experiment. Done
   when: `specs/<id>/spec.md` is readable.

2. **Read the fence.** Read `specs/<id>/spec.md` in full, then `specs/<id>/tasks.md` and the run records under
   `experiments/<id>/runs/` when they exist. The plan serves the spec's question within its constraints and budget. Done
   when: the question, constraints, completion criteria and remaining budget (`just budget <id>`) are known.

3. **Write the plan.** Rewrite `specs/<id>/plan.md` from `$ARGUMENTS` and what the evidence so far shows, keeping the
   three sections of the template (`Current strategy`, `Candidate runs`, `What would change the plan`). Replace outdated
   strategy rather than appending to it; the old version stays in Git. Each candidate run states what it would decide
   and a rough cost in the budget unit; candidates whose summed cost exceeds the remaining budget are marked as such.
   Done when: the plan reads as one current strategy, with no two sections contradicting each other.

4. **Report spec conflicts.** When the new strategy requires something the spec forbids or lacks (a data source, a
   different protocol, more budget), stop and list it for the human; the Experiment continues only after the spec is
   edited and re-approved, or the strategy changes to fit. Done when: either no conflict exists or the human has the
   list.

5. **Commit** `specs/<id>/plan.md` on branch `<id>` with title `exp-NNN: update plan`. Done when: the working tree is
   clean.

Next: `/speckit-tasks` to update the ledger, or `/speckit-implement` to continue iterating.
