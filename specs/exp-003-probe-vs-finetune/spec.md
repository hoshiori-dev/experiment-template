---
experiment: exp-003-probe-vs-finetune
issue: 3
budget:
  unit: gpu-hours
  limit: 0.4
holdout: "Test images are evaluated only by Formal Runs and by informal runs started after the design file is committed; no test number is used to change the design."
---

# Experiment spec: exp-003-probe-vs-finetune

Normative. Every rule below is part of the fence: if it is violated, the Experiment is not complete even when the result
looks good. Any edit to this file after approval invalidates the approval; re-run `/speckit-research-approve` before the
next Formal Run.

Test for what belongs here: a sentence goes in the spec when breaking it would void the Experiment; otherwise it goes in
`plan.md`.

## Question

On a class-balanced subset of Food-101, which adaptation of an ImageNet-pretrained ResNet-18 reaches higher top-1 test
accuracy: a linear probe on frozen features, or fine-tuning the last residual block together with the classifier?

## Why now and how it belongs to the Epic

Epic #1 asks what a small ImageNet-pretrained network reaches on Food-101 with little compute and how much of that comes
from adapting the features rather than only reading them out. This is the comparison its exit criteria name, and it lies
inside its scope: adaptation depth (linear probe against partial fine-tuning) on class-balanced subsets, with the
learning rate as the only tuned hyperparameter. The answer closes the Epic's exit criteria and tells the next round
whether deeper adaptation is worth its cost on this task.

## Constraints

- Data: `ethz/food101` from the Hugging Face Hub at revision `83488de741c1bd1ce27aa6a2b33e19c7bdf92ca9`, the first of
  the Epic's two allowed inputs. Training and tuning images come from its `train` split, test images from its
  `validation` split. The subset is class-balanced over all 101 classes and is defined by a manifest of image
  identifiers committed in `experiments/exp-003-probe-vs-finetune/`; each run record declares the dataset revision and
  the manifest's SHA-256.
- Model: torchvision ResNet-18 with the `IMAGENET1K_V1` weights, file `resnet18-f37072fd.pth`, the second allowed input.
  Each run record declares the file's full SHA-256, which begins with `f37072fd`.
- Protocol: both arms use the same training images, the same tuning split, the same test images, the same input size,
  the same number of epochs, the same learning-rate grid and the same seeds. The tuning split is held out from the
  training subset: its images are never trained on. The learning rate is the only tuned hyperparameter and is selected
  per arm on the tuning split. Each arm is trained with at least three seeds. The metric is top-1 accuracy on the test
  images.
- Comparison rules: an arm's result is the mean and the standard deviation of its test accuracy over the seeds, at the
  learning rate selected on the tuning split. Arms are compared only through the rule in "Completion criteria".
- Held-out data protection: the test images take no part in training or in model selection. The design file (subset
  manifest, tuning split, epochs, learning-rate grid, seeds) is committed before any run, formal or informal, evaluates
  a test image, and is not changed afterwards on the strength of a test number. Sizing runs skip test evaluation. A
  design change made after a test number was seen is reported as a deviation in the README's limits section.

## Completion criteria

Let `d` be the difference between the two arms' mean test accuracies in percentage points, and `s` the larger of the two
standard deviations. One arm is higher when `|d| > 1.0` and `|d| > 2 s`; the answer then names that arm and both means.
Otherwise the answer is "inconclusive". The numbers come from Formal Runs only.

## Stop conditions

- The budget limit is reached before both arms have three seeds each.
- The protocol cannot be kept inside the budget at any subset size that still covers all 101 classes.
- Either input cannot be fetched at its declared version.

## Budget

0.4 gpu-hours for the whole Experiment, within the 0.5 gpu-hours planned on issue #3 and the Epic's per-Experiment
allotment of 0.5. Formal Runs reserve against this limit; splitting work into more runs adds nothing to it.

## Out of scope

Other architectures, full-dataset training, data augmentation studies, hyperparameters other than the learning rate,
fine-tuning depths other than the last residual block.
