---
description: Update the rolling task ledger (T001...) of the current Experiment; done and abandoned entries stay.
argument-hint: "Experiment ID (defaults to the current branch), then optional tasks or state changes"
---

## User Input

```text
$ARGUMENTS
```

## Role and goal

You maintain `specs/<id>/tasks.md`, the rolling ledger of an Experiment. The ledger is operational, not a plan to
complete: it shows what was done, what is in progress, what was abandoned and why. Finishing the Experiment never
requires an empty ledger.

## Ledger rules

- IDs are `T001`, `T002`, ... in order of creation; a number is never reused, including numbers of removed `planned`
  tasks.
- States: `planned`, `in progress`, `done`, `abandoned (reason)`.
- A `planned` task may be edited or removed. A `done` or `abandoned` task is never deleted or rewritten; a correction is
  a new task.
- A task that produced a Formal Run names the run ID (`R###`) in its notes.

## Steps

1. **Locate the Experiment.** `<id>` is the first word of `$ARGUMENTS` when it has the form
   `exp-NNN-<slug>`; when it is left out, `<id>` is the current branch name, which must then be `exp-NNN-<slug>`. An
   `<id>` given as an argument must equal the current branch; when they differ, or the branch is not an Experiment
   branch and no `<id>` was given, stop and report without changing a file. No pointer file is read. Done
   when: `specs/<id>/tasks.md` is readable, or is created
   from the template (`.specify/scripts/bash/resolve-template.sh tasks-template`, fallback
   `.specify/presets/research/templates/tasks-template.md`).

2. **Apply the change.** From `$ARGUMENTS`, `specs/<id>/plan.md` and the current state of the work, add new tasks with
   the next free numbers, move states forward, and record reasons for every `abandoned`. Done when: every row has an ID,
   a state from the list above, and every `abandoned` row has a reason.

3. **Commit** `specs/<id>/tasks.md` on branch `<id>` with title `exp-NNN: update tasks`. Done when: the working tree is
   clean.

Next: `/speckit-implement` to continue iterating.
