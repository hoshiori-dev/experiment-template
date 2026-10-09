---
experiment: exp-NNN-slug # Experiment ID; same string as specs/<id>/, experiments/<id>/ and the branch
issue: NNN # experiment issue number in the main repository
budget: # omit the whole block when the Epic says "unlimited"
  unit: gpu-hours # the unit the Epic defines
  limit: 0.0 # binding upper bound for the whole Experiment; at most the issue allotment
holdout: "How held-out data is protected from informal runs; one or two sentences."
---

# Experiment spec: exp-NNN-slug

Normative. Every rule below is part of the fence: if it is violated, the Experiment is not complete even when the result
looks good. Any edit to this file after approval invalidates the approval; re-run `/speckit-research-approve` before the
next Formal Run.

Test for what belongs here: a sentence goes in the spec when breaking it would void the Experiment; otherwise it goes in
`plan.md`.

## Question

One precise question this Experiment answers. Name the thing compared, the measure, and the data.

## Why now and how it belongs to the Epic

Which Epic (issue number) this serves, which part of its objective and scope this question falls under, and what the
answer changes for the next step.

## Constraints

- Data: each input with its exact version (content hash, commit, manifest digest), and its source within the Epic's
  allowed sources and licences.
- Protocol: what both arms share (training set, epochs, search grid, seeds, metric), so the comparison is fair.
- Comparison rules: how arms are compared and what counts as a difference.
- Held-out data protection: what is held out, when the design is frozen relative to the first look at held-out numbers,
  and how a deviation is reported (in the README's limits section).

## Completion criteria

The pre-registered decision rule. Written before any run that touches held-out data; it decides between the possible
answers, including "inconclusive", from numbers the Formal Runs will produce.

## Stop conditions

When this Experiment stops short of its criteria: budget exhausted; the question is unanswerable under the constraints;
a constraint turns out impossible to keep. Add Experiment-specific conditions.

## Budget

The front-matter limit in words: the unit, the limit, and the issue allotment it stays within. Formal Runs reserve
against this limit; splitting work into more runs adds nothing to it.

## Out of scope

What this Experiment deliberately leaves to other Experiments or a later Epic.
