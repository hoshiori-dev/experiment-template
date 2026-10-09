---
name: speckit-research-finish
description: Close out an Experiment - README deletion test, evidence citations, traceability check, hand over.
compatibility: Requires spec-kit project structure with .specify/ directory
metadata:
  author: experiment-template
  source: research:commands/speckit.research.finish.md
---

## User Input

```text
$ARGUMENTS
```

## Role and goal

You close one Experiment so that its directory explains and supports its own conclusion. Finishing does not require
every task done; it requires that `experiments/<id>/README.md` passes the deletion test: if `specs/<id>/` were deleted,
a reader of the README alone still knows what was studied, what was run, where the evidence is, what the conclusion is,
what its limits are, and how to reproduce it. Read `.agents/knowledge/evidence.md` for what counts as evidence and
`.agents/knowledge/governance.md` for the hand-over rules.

## Steps

1. **Locate.** `$ARGUMENTS` names `<id>`; otherwise resolve it from `.specify/feature.json` or the branch name. Confirm
   `git branch --show-current` is `<id>` and the tree is clean. Done when: `<id>` is known and `git status --porcelain`
   is empty.

2. **No unmerged run branches.** `git branch --all --list 'run/<id>/*'` lists only branches whose record on `<id>`
   carries an outcome. A run still without outcome is finished first (`/speckit-research-run` step 7-8) or recorded
   `aborted` with `actual_usage` 0 and merged. Done when: every record under `experiments/<id>/runs/` has an outcome and
   `just budget <id>` passes.

3. **README.** Edit `experiments/<id>/README.md` so the six fixed sections hold real content: `Question`,
   `What was run`, `Evidence`, `Conclusion`, `Limits and remaining uncertainty`, `Reproduce`. The status line takes one
   of `answered`, `answer is negative`, `inconclusive` (or stays `in progress` when the Experiment is handed back
   unfinished, with the remaining work named). Every conclusion cites the Formal Run that supports it by `R###`, with
   the key numbers quoted from the tracker; a claim resting on an informal run is removed or rewritten as a hypothesis.
   A failed or aborted run is described by what it showed, not called "informative" without that. Deviations from the
   spec's design (for example a look at held-out numbers before freezing) go under limits. Done when: each conclusion
   sentence names an `R###`, and the README answers the six questions without the spec.

4. **Ledger.** In `specs/<id>/tasks.md`, each remaining task is `abandoned (reason)` or stays `planned`; `planned`
   leftovers are summarized in the README as follow-up work. `done` and `abandoned` rows stay untouched. Done when: no
   row is `in progress`.

5. **Traceability.** For each `completed` run: `just source-commit <id> R### --verify-tracker` prints the commit that
   added the record and confirms the tracker's `source_commit` equals it. A mismatch is reported to the human as is; the
   record and the tracker are never edited to agree. Done when: every completed run verifies, or the mismatch is in the
   hand-over note.

6. **Checks and commit.** `just validate-records`, `just budget <id>`, `just check`. Commit with title
   `exp-NNN: close out` (the short form of `<id>` as scope). Done when: all three pass and the tree is clean.

7. **Actual usage to the issue.** Total `actual_usage` over all records is the Experiment's usage. Write a comment draft
   at `.local/drafts/<id>-usage.md`: the status line, the usage and unit, the limit, and a link to the README path; run
   `just outbound` on it. With external writes on (the shipped default), post it with `gh issue comment N --body-file`.
   Done when: the number is on the issue or in the draft.

## Hand-over

Stop. The pull request for branch `<id>` is merged into `main` with a merge commit (never squash or rebase: run
references point at these commits). High-automation mode (the shipped default): the agent merges with
`gh pr merge <pr> --merge` only when the PR touches nothing outside `specs/<id>/` and `experiments/<id>/`; otherwise the
human merges. Human-led mode: the human reviews and merges. Update the PR body from `.local/drafts/<id>-pr.md` with the
status line and usage before the merge.
