---
description: Synthesize an Epic - rendezvous commit, evidence selection, proposed changes to docs/, PR draft.
argument-hint: "Epic issue number"
---

## User Input

```text
$ARGUMENTS
```

## Role and goal

You turn the finished Experiments of one Epic into a proposed change to the accepted experiment knowledge in `docs/`.
The proposal becomes knowledge only when a human merges it (the Acceptance Gate); you stop before that. Read
`.agents/knowledge/governance.md` for the gate and `.agents/knowledge/publishing.md` before the PR draft.

## Steps

1. **Epic and rendezvous commit.** `$ARGUMENTS` names the Epic number `E`; ask when missing. The rendezvous commit is
   the current tip of `main` (`git fetch` then `git rev-parse origin/main`) after every Experiment of the Epic that
   counts has been merged; confirm the hash with the human before continuing. It is recorded by branch ancestry only,
   never written into a file. Done when: the human confirmed hash `<sha>`.

2. **Branch.** `git switch -c synthesis/E <sha>`. From here on, nothing is merged or cherry-picked from later research
   commits; a result arriving later waits for the next synthesis. Done when: `git merge-base --is-ancestor <sha> HEAD`
   holds and HEAD equals `<sha>`.

3. **Evidence selection.** List every Experiment under the Epic (`gh issue view E --json subIssues`, then
   `experiments/exp-NNN-*/README.md`). Decide which Experiments and which of their conclusions are included, which are
   excluded, and why (status line, limits, hold-out deviations, failed runs). Write this list into the PR draft (step
   6); selection is part of the reasoning and is shown, not implied. Done when: every sub-issue appears as included or
   excluded with a reason.

4. **Write to `docs/`.** Create or edit files under `docs/` only (and `README.md` of `docs/` when it exists). Style of
   `docs/`: concise and dense, stable terms; each statement says what is now accepted and which evidence supports it,
   linking to the Experiment README (`experiments/<id>/README.md`) and run IDs; keep only the qualifiers that change how
   the knowledge is used; no run-by-run narrative, no Epic history, no index of Experiments; when new evidence overturns
   an older statement, change or delete the old statement in place. Done when: every statement in the diff links to a
   README and no excluded Experiment is cited.

5. **Commit** on `synthesis/E` with title `docs: synthesize epic E` (one or more commits, all under `docs/`). Done when:
   `git diff <sha> --name-only` lists only paths under `docs/`.

6. **PR draft.** Write `.local/drafts/synthesis-E-pr.md`: the rendezvous hash, the inclusions and exclusions from step
   3, the proposed changes in one paragraph, and open questions that may open the next Epic. Run
   `just outbound .local/drafts/synthesis-E-pr.md` and fix findings. Done when: the draft passes.

7. **Harness check-up, separately.** Read `.agents/skills/harness-checkup/SKILL.md` and run it as it directs. Its
   findings go to the note the skill writes, `.local/drafts/harness-checkup-<YYYY-MM-DD>.md`, and its proposed fixes to
   the branch `harness/checkup-<YYYY-MM-DD>`, never to `synthesis/E`: harness changes are their own branch and their own
   review. Done when: the note exists, even when it reports nothing to change.

## Hand-over

Stop before merging. External writes on (the shipped default): push and
`gh pr create --title "docs: synthesize epic E" --label synthesis --body-file .local/drafts/synthesis-E-pr.md`, then
stop; the merge is the human's act in every governance model. External writes off: the human pushes `synthesis/E`, opens
the pull request with the draft body and label `synthesis`, reviews, and merges with a merge commit. Until merged,
nothing in `docs/` on this branch is accepted knowledge.
