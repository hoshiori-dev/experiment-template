---
name: speckit-research-experiments
description: Propose the Experiments of a published Epic and create their experiment issues as sub-issues.
compatibility: Requires spec-kit project structure with .specify/ directory
metadata:
  author: experiment-template
  source: research:commands/speckit.research.experiments.md
---

## User Input

```text
$ARGUMENTS
```

## Role and goal

In high-automation governance you decide which Experiments a published Epic needs. Done means: every proposed Experiment
is an open sub-issue of the Epic with a goal, a reason it belongs to the Epic, and a planned allotment, and the
allotments fit the Epic's total. Each issue then starts an Experiment with `/speckit-specify <issue-number>`. Read
`.agents/knowledge/research-loop.md` (Epic and experiment issues) and `.agents/knowledge/governance.md` (budget,
stopping rules) before the first proposal.

## Steps

1. **Confirm the Epic is valid.** Take the Epic number `E` from `$ARGUMENTS` and run `just epic-status E`. Exit 1 or 2
   stops this command: say why and what the human has to do. Done when: `just epic-status E` exits 0.

2. **Read the fence.** `gh issue view E --json title,body,labels,subIssues` gives objective, scope, constraints (allowed
   data sources and licences), budget policy (unit, total, per-Experiment allotment, or "unlimited") and exit criteria.
   List the sub-issues that already exist and, for each, read its planned allotment and, when it has a spec on a branch,
   the spec's `budget.limit` and actual usage comments. Done when: you can state how much of the total is still
   unplanned.

3. **Propose Experiments.** Each proposal answers one concrete question that advances the exit criteria, fits the scope
   as written (membership must be decidable from the scope text alone), stays inside the constraints, and gets an
   allotment at most the per-Experiment allotment. Prefer few, decisive Experiments over many small ones; name what each
   would change in the accepted knowledge under `docs/` if it succeeds or fails. The sum of allotments over all open
   sub-issues stays at or below the Epic total. Done when: the list, with allotments and the running sum, is written to
   `.local/drafts/epic-E-experiments.md`.

4. **Outbound review.** Run `just outbound .local/drafts/epic-E-experiments.md`, then read it through with the
   `outbound-review` skill. Done when: both pass; otherwise rewrite and repeat.

5. **Create the issues.** For each proposal, in the field order of `.github/ISSUE_TEMPLATE/experiment.yml` (Goal, Why it
   belongs to the Epic, Planned allotment, Parent Epic number), run
   `gh issue create --parent E --label experiment --title "<goal in one line>" --body-file <file>` with the body written
   to `.local/drafts/exp-<slug>-issue.md` first. Done when: `gh issue view E --json subIssues` lists every new issue.

6. **Hand over.** Report the issue numbers and allotments, the remaining unplanned budget, and which issue you start
   first with `/speckit-specify <number>`. With external writes off, stop after step 4 and hand the draft to the human,
   who creates the issues.

## Stop points

- The Epic's remaining budget does not fit any Experiment that could still advance the exit criteria: do not create
  issues; comment on the Epic (`gh issue comment E`) with the shortfall and stop the loop.
- A proposal needs a data source or licence outside the Epic's allowed list: leave it out and name it in the hand-over
  for the owner to decide.
