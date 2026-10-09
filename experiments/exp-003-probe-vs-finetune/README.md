# exp-003-probe-vs-finetune

Status: in progress

## Question

On a class-balanced subset of Food-101, which adaptation of an ImageNet-pretrained ResNet-18 reaches higher top-1 test
accuracy: a linear probe on frozen features, or fine-tuning the last residual block together with the classifier?

Decision rule, fixed before any formal run: with `d` the difference of the two arms' mean test accuracies in percentage
points and `s` the larger of their standard deviations over seeds, one arm is higher when `|d| > 1.0` and `|d| > 2 s`;
otherwise the answer is inconclusive.

## What was run

Each formal run by ID with its decision, source commit and outcome; informal runs are mentioned only as context.

## Evidence

The few key numbers the conclusion rests on, each with the formal run it comes from (the tracker is the source; these
are citations).

## Conclusion

The answer to the question, as the decision rule yields it; negative and inconclusive answers are reported as such.

## Limits and remaining uncertainty

Deviations from the spec, workarounds of shared parts, what the evidence does not cover, and planned follow-up work.

## Reproduce

The source commit and run record to start from, the data inputs with their declared versions, and the build and launch
steps as actually used.
