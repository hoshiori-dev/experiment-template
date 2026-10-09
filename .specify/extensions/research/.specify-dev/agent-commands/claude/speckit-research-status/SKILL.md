---
name: speckit-research-status
description: Read-only research status - experiments, runs, budgets, Epic validity; changes nothing.
compatibility: Requires spec-kit project structure with .specify/ directory
metadata:
  author: experiment-template
  source: research:commands/speckit.research.status.md
---

## User Input

```text
$ARGUMENTS
```

## Role and goal

You report where the research stands. This command reads and summarizes; it writes no file, makes no commit, and sends
nothing. State is computed from the repository every time, never from a stored table.

## Steps

1. **Repository status.** Run `just status`. It lists the Experiments found under `specs/` and `experiments/`, each
   README's status line, runs with their outcomes, budget spent against limit, unmerged run branches and open synthesis
   branches. Done when: the output is in hand.

2. **Epic validity.** For each Epic number the human named in `$ARGUMENTS`, run `just epic-status <n>`. Exit 0 is valid;
   exit 1 prints why not; exit 2 means unreachable, reported as "unknown", never as valid. When no Epic is named, skip
   this step and say so. Done when: every named Epic has a verdict.

3. **Summarize** in the conversation, in this order: Epics and their validity; Experiments grouped by status line
   (`in progress`, `answered`, `answer is negative`, `inconclusive`) with runs, outcomes and budget spent/limit;
   unmerged run branches and open synthesis branches as items that need attention; anything `just status` flagged. Done
   when: the summary fits on one screen and every number traces to a command output above.

Next acts: the human decides; no file changed.
