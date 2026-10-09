# Plan: exp-003-probe-vs-finetune

Advisory. This file holds the current strategy and is rewritten whenever evidence changes it; its Git history is the
record of how thinking moved. Nothing here binds the Experiment: the binding rules are in `spec.md`.

## Current strategy

One training script with an `--arm` switch, read top to bottom: load the manifest, build the model, freeze what the arm
freezes, train, select the learning rate on the tuning split, evaluate the test images once per seed. Sizes are chosen
by informal sizing runs that skip test evaluation, so that one Formal Run covering both arms fits well inside the
budget. First write and commit the design file (manifest, split, epochs, grid, seeds); only then run anything that
touches test images.

Starting point for the design, to be settled by sizing: about 100 training images per class with a fifth held out for
tuning, about 50 test images per class, a small learning-rate grid, three seeds.

## Candidate runs

Runs under consideration, in rough order, each with what it would decide and a rough cost in the budget unit. A
candidate becomes a Formal Run through `/speckit-research-run`; informal runs need no entry.

| Candidate                  | Decides                                   | Rough cost | Status     |
| -------------------------- | ----------------------------------------- | ---------- | ---------- |
| both arms, grid, 3 seeds   | the question, by the spec's decision rule | 0.2        | considered |
| repeat with two more seeds | the question, if the first is borderline  | 0.15       | considered |

## What would change the plan

Sizing shows the grid times seeds does not fit: shrink the subset before shrinking the seeds. No usable GPU: the run
does not start; a CPU run would be a new decision with its own record and a much smaller subset.
