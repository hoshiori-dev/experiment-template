# Plan: exp-003-probe-vs-finetune

Advisory. This file holds the current strategy and is rewritten whenever evidence changes it; its Git history is the
record of how thinking moved. Nothing here binds the Experiment: the binding rules are in `spec.md`.

## Current strategy

One training script with an `--arm` switch, read top to bottom: load the manifest, build the model, freeze what the arm
freezes, train, select the learning rate on the tuning split, evaluate the test images once per seed. Sizes are chosen
by informal sizing runs that skip test evaluation, so that one Formal Run covering both arms fits well inside the
budget. First write and commit the design file (manifest, split, epochs, grid, seeds); only then run anything that
touches test images.

Sizing settled the design: 80 fit, 20 tuning and 50 test images per class, 10 epochs, batch size 128, learning rates
0.001 to 0.3 in six steps, seeds 0 to 2. The whole grid for both arms takes about five minutes on one GPU. The first
grid (0.0001 to 0.03) put both arms' best tuning accuracy at its top edge, so it was moved up until the best value sat
inside it; only tuning-split numbers were used for that.

## Candidate runs

Runs under consideration, in rough order, each with what it would decide and a rough cost in the budget unit. A
candidate becomes a Formal Run through `/speckit-research-run`; informal runs need no entry.

| Candidate                  | Decides                                   | Rough cost | Status     |
| -------------------------- | ----------------------------------------- | ---------- | ---------- |
| both arms, grid, 3 seeds   | the question, by the spec's decision rule | 0.1        | next       |
| repeat with two more seeds | the question, if the first is borderline  | 0.15       | considered |

## What would change the plan

Sizing shows the grid times seeds does not fit: shrink the subset before shrinking the seeds. No usable GPU: the run
does not start; a CPU run would be a new decision with its own record and a much smaller subset.
