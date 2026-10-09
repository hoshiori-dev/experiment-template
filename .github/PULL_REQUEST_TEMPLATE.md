<!--
Keep the section for this PR's kind and delete the other one.
Merge with a merge commit (no squash, no rebase): run records and the rendezvous commit
point at commits on this branch, and squashing or rebasing loses them.
-->

## Experiment PR

- Experiment ID: `exp-NNN-<slug>`
- Experiment issue: #NNN
- Spec approval: pending / approved (label `spec:approved` on this PR; re-approval needed after any spec change)

### Formal runs

| Run  | Decision                   | Outcome   | Actual usage |
| ---- | -------------------------- | --------- | ------------ |
| R001 | (one sentence from record) | completed | 0.0          |

- Actual usage total (spec unit): 0.0 of limit 0.0 — write this number back to the experiment issue when closing out
- Unmerged run branches: none

### Deviations and workarounds

- Shared-library or check defects bypassed inside this experiment's directory, and what the next preparation phase
  should fix: none
- Deviations from the approved spec (also recorded in README "Limits and remaining uncertainty"): none

## Synthesis PR

Label: `synthesis`.

- Epic: #NNN
- Rendezvous commit: `<full sha on main>` (this branch starts there; nothing merged or cherry-picked since)

### Evidence

- Included experiments and why:
- Excluded experiments and why:

### Open questions

- Candidates for the next Epic:
