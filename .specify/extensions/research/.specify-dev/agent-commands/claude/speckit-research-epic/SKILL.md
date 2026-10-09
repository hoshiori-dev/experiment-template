---
name: speckit-research-epic
description: Draft an Epic (objective, scope, constraints, budget policy, exit criteria) for a maintainer to publish.
compatibility: Requires spec-kit project structure with .specify/ directory
metadata:
  author: experiment-template
  source: research:commands/speckit.research.epic.md
---

## User Input

```text
$ARGUMENTS
```

## Role and goal

You draft the plan for one round of research as an Epic. Publishing is the maintainer's act: adding the label
`epic:approved` to the issue after it was created. Done means: a complete draft in the issue-form field order sits in
`.local/drafts/epic-<slug>.md`, has passed the outbound check, and names every gap the maintainer still has to fill.
Read `.agents/knowledge/governance.md` for what an Epic is and when it counts as valid.

## Steps

1. **Gather input.** Take the direction from `$ARGUMENTS` and the conversation. When `docs/` exists, read the accepted
   experiment knowledge there: the Epic builds on what is accepted and names the open questions it attacks. Ask the
   human for whatever the five fields below need and the input lacks, except budget numbers (step 3). Done when: each
   field has either content or a named gap.

2. **Write the draft** at `.local/drafts/epic-<slug>.md` (`<slug>`: two to four lowercase words joined by `-`), fields
   in the order of the issue form `.github/ISSUE_TEMPLATE/epic.yml`:
   - **Objective**: what this round settles and why now.
   - **Scope**: which Experiments belong and which explicitly do not, precise enough that an approver can decide
     membership of a spec without asking.
   - **Constraints**: data, models, protocol and comparison rules every Experiment follows, including the allowed data
     sources and licence range.
   - **Budget policy**: unit, total cap for the Epic, allotment per Experiment. Unlimited is written as "unlimited",
     never left blank.
   - **Exit criteria**: when synthesis may start. Required: without it nobody can tell when to stop
     opening Experiments. Done when: every field heading is present.

3. **Budget numbers come from the maintainer.** Where the human gave none, write the line
   `Budget policy: to be filled by the maintainer before publishing` under the field; the unit may be proposed, the
   numbers never. Done when: no budget number in the draft lacks a human source.

4. **Completeness check.** Report each item as present or missing, in
   `.local/drafts/epic-<slug>-check.md` and in the conversation (a separate file, so the check never becomes part of
   the Epic body):
   - budget policy written (unit, total, per-Experiment allotment, or "unlimited");
   - scope decidable: a reader can tell whether a given Experiment belongs;
   - allowed data sources and licence range written;
   - exit criteria written when AGENTS.md "Current settings" names high-automation mode. A gap found now is cheap; the
     same gap found during the experiment phase stops an agent until a human answers. Done when: the check lists all
     four items with a verdict.

5. **Outbound check.** Read `.agents/knowledge/publishing.md`, then run `just outbound .local/drafts/epic-<slug>.md`. On
   findings, rewrite and run again; report only rule and location, never the matched content. Done when: the check
   passes.

## Hand-over

With external writes on (the shipped default), create the issue with
`gh issue create --title "<title>" --label epic --body-file .local/drafts/epic-<slug>.md` and tell the maintainer which
number to review and what the completeness check found. With external writes off, hand both drafts to the maintainer,
who creates the issue from the form "Epic". Either way stop here: the maintainer fills the budget and adds
`epic:approved` after creation, and that label is always the maintainer's act. The body is frozen from that moment;
later clarifications go into comments.
