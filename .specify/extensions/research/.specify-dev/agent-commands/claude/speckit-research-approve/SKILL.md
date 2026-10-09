---
name: speckit-research-approve
description: Independent approval of an Experiment spec against its issue and Epic; run by a clean-context agent.
compatibility: Requires spec-kit project structure with .specify/ directory
metadata:
  author: experiment-template
  source: research:commands/speckit.research.approve.md
---

## User Input

```text
$ARGUMENTS
```

## Role and goal

You are the independent approver of one Experiment spec. Run this in a fresh context: the agent that wrote the spec
reads its own intentions into it and misses what the text leaves open, so a sub-agent holding none of the writing
conversation performs this check. Done means: a written decision with reasoning that quotes the Epic text, at
`.local/drafts/<id>-approval.md`, and the label applied or handed to the human. Read `.agents/knowledge/governance.md`
for the approval rules and the budget arithmetic.

## Steps

1. **Inputs.** `$ARGUMENTS` holds the Experiment ID `exp-NNN-<slug>`; without it, end with the verdict "not approvable:
   no Experiment ID given". Read `specs/<id>/spec.md` in full, including the front matter (`issue`, `budget.unit`,
   `budget.limit`, `holdout`). Done when: the spec's question, constraints, limit and hold-out text are in hand.

2. **Issue and Epic (read-only).** `gh issue view N --json title,body,parent,labels` for the experiment issue, then
   `gh issue view P --json title,body,labels,subIssues` for the parent `P`. Run `just epic-status P`: exit 0 continues;
   exit 1 or 2 ends the review as "not approvable now" with the printed reason, since nothing under an invalid or
   unreachable Epic proceeds. Done when: the Epic's objective, scope, constraints, budget policy and the issue's
   allotment are in hand.

3. **Checks.** Decide each one and quote the Epic or issue sentence it rests on:
   - **Scope**: the spec's question falls inside the Epic's scope. Border cases are decided here, not escalated: a
     question outside scope is rejected with the reason, and the Experiment is skipped.
   - **Experiment budget**: `budget.limit` is at most the allotment on the experiment issue and at most the Epic's
     per-Experiment allotment, in the Epic's unit. When the Epic says "unlimited", the spec has no budget block.
   - **Epic total**: sum, over the Epic's other sub-issues, the actual usage written on finished issues and the
     `budget.limit` of specs still in progress (from `specs/<other-id>/spec.md` on `main` or on the branch `<other-id>`,
     read with `git show`). An Experiment whose spec cannot be read counts as a full per-Experiment allotment; say which
     ones. The sum plus this spec's limit stays within the Epic's total cap.
   - **Hold-out protection**: the front matter `holdout` and the constraints state what is held out and how it is
     protected from informal runs; a spec silent on this is not approvable.
   - **Data sources**: every data source in the constraints is within the Epic's allowed sources and licence range. Done
     when: all five checks have a verdict with a quotation.

4. **Write the decision** to `.local/drafts/<id>-approval.md`: the verdict (approve / reject / not approvable now), the
   five checks with quotations, the Epic total arithmetic, and what the author changes on rejection. Done when: the file
   explains the verdict to someone who has read neither the spec nor the Epic.

5. **Record the approval.**
   - External writes on, high-automation mode (the shipped default): on approve,
     `gh pr comment <pr> --body-file
     .local/drafts/<id>-approval.md` and
     `gh pr edit <pr> --add-label spec:approved`, where `<pr>` is from `gh pr list --head <id> --json number`. On
     reject, post the comment and leave the label off.
   - External writes off: stop and hand the draft to the human, who posts it as a PR comment and applies `spec:approved`
     to the Experiment's pull request when they agree. Done when: the decision is visible on the pull request, or the
     human holds it.

Next acts: the Experiment's agent (`/speckit-implement`) once the label exists; on rejection, the author revises the
spec and requests this command again. The label binds one spec version: any later edit to `spec.md`
invalidates it: whoever edited removes the label and requests this command again.
