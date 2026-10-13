# exp-003-probe-vs-finetune

Status: answered

## Question

On a class-balanced subset of Food-101, which adaptation of an ImageNet-pretrained ResNet-18 reaches higher top-1 test
accuracy: a linear probe on frozen features, or fine-tuning the last residual block together with the classifier?

Decision rule, fixed before any formal run: with `d` the difference of the two arms' mean test accuracies in percentage
points and `s` the larger of their standard deviations over seeds, one arm is higher when `|d| > 1.0` and `|d| > 2 s`;
otherwise the answer is inconclusive.

This Experiment belongs to Epic #1 (transfer learning baselines on Food-101); its issue is #3.

## What was run

One Formal Run.

| Run  | Decision                                                  | Source commit | Outcome   | Usage           |
| ---- | --------------------------------------------------------- | ------------- | --------- | --------------- |
| R001 | which arm has the higher test accuracy, by the rule above | `37529bf`     | completed | 0.091 gpu-hours |

R001 trained both arms under the design in `design.json`: 80 training, 20 tuning and 50 test images for each of the 101
classes (8080, 2020 and 5050 images), drawn by a seeded generator from the pinned dataset revision; input resized to 256
and centre-cropped to 224 with no augmentation; 10 epochs of SGD with momentum 0.9, a cosine schedule and batch size
128; learning rates 0.001, 0.003, 0.01, 0.03, 0.1 and 0.3; seeds 0, 1 and 2. Tuning images are never trained on. For
each arm the learning rate with the highest mean tuning accuracy was selected, and only models at that learning rate
were evaluated on the test images.

Both arms freeze the network up to and including `layer3`, so `train.py` computes that part's output once per image and
trains on the stored activations. The linear probe also keeps `layer4` frozen, in evaluation mode, and trains only a new
101-way classifier; the fine-tuning arm trains `layer4` and the classifier.

Before R001, two informal sizing runs were made. Neither loaded a test image.

## Evidence

All numbers are from R001 (tracker project `exp-003-probe-vs-finetune`, run `R001`; the same values are kept in
`results/R001.json`).

| Arm                  | Selected learning rate | Mean tuning accuracy | Test accuracy per seed | Test mean | Test std |
| -------------------- | ---------------------- | -------------------- | ---------------------- | --------- | -------- |
| linear probe         | 0.03                   | 52.10                | 55.39, 55.43, 55.86    | 55.56     | 0.26     |
| fine-tune last block | 0.03                   | 58.00                | 63.25, 63.01, 62.10    | 62.79     | 0.61     |

Accuracies are top-1, in percent. For both arms the selected learning rate lies inside the grid: tuning accuracy falls
on either side of it.

## Conclusion

Fine-tuning the last residual block is higher (R001). The difference of the means is `d = 62.79 - 55.56 = 7.23`
percentage points; the larger standard deviation is `s = 0.61`. Both conditions of the rule hold: `7.23 > 1.0` and
`7.23 > 2 x 0.61 = 1.22`.

## Limits and remaining uncertainty

- The answer to this comparison was known in advance. An earlier, unpublished run of the same comparison exists on this
  machine, and its numbers were seen before this Experiment was designed. The decision rule and the design were written
  without using them, and the spec's protection covers only test numbers produced by this Experiment, so this is
  reported here rather than counted as a deviation. As an independent confirmation the result is weaker than it looks.
- The learning-rate grid was changed once before the design was committed. The first sizing run used 0.0001 to 0.03 and
  both arms were best at 0.03, the top edge, so the grid was moved up. Only tuning-split numbers were used.
- One subset draw. The standard deviations measure variation over classifier initialisation and batch order on a fixed
  set of images, not over the choice of images, so the uncertainty of the 7.23-point difference with respect to the
  subset is not measured.
- Three seeds per arm, the minimum the spec asks for.
- The result is for 80 training images per class, 10 epochs and no augmentation. It says nothing about the full dataset
  or longer training.
- Workaround of a shared part: the commit titles the run procedure prescribes (`exp-NNN: R### source`,
  `exp-NNN: R### <outcome>`) are rejected by the commit-message hook, which requires a lowercase first word. The run's
  commits are titled `exp-003: run R001 source` and `exp-003: record R001 completed` instead. To be fixed in the next
  preparation phase.
- Follow-up not done: repeating with more seeds or a second subset draw. The budget would allow it (0.091 of 0.4
  gpu-hours used).

## Reproduce

Start from the source commit `37529bf811d42fbf4cb0914f5ce3c1ff234193cb` and the record `runs/R001.yaml`.

Inputs, placed under `.local/data/` with a `VERSION` file holding the version string:

| Name                     | Source                                                      | Version                                                                   |
| ------------------------ | ----------------------------------------------------------- | ------------------------------------------------------------------------- |
| `food101`                | `ethz/food101` on the Hugging Face Hub                      | revision `83488de741c1bd1ce27aa6a2b33e19c7bdf92ca9`                       |
| `resnet18-imagenet1k-v1` | `https://download.pytorch.org/models/resnet18-f37072fd.pth` | `sha256:f37072fd47e89c5e827621c5baffa7500819f7896bbacec160b1a16c560e07ec` |

Steps as actually used, from the repository root, with one GPU and a driver that supports CUDA 13:

```sh
ID=exp-003-probe-vs-finetune
SHA=37529bf811d42fbf4cb0914f5ce3c1ff234193cb
mkdir -p .local/runs/$ID/R001/source .local/runs/$ID/R001/out .local/trackio
git archive $SHA:experiments/$ID | tar -x -C .local/runs/$ID/R001/source
docker build --build-arg RUN_ID=R001 -t exp-003:R001 .local/runs/$ID/R001/source
docker run --rm --gpus all --network none --read-only --tmpfs /tmp --shm-size 2g \
  --user "$(id -u):$(id -g)" \
  -v "$PWD/.local/data/food101:/data/food101:ro" \
  -v "$PWD/.local/data/resnet18-imagenet1k-v1:/data/weights:ro" \
  -v "$PWD/.local/runs/$ID/R001/out:/out" \
  -v "$PWD/.local/trackio:/trackio" \
  -e TRACKIO_DIR=/trackio -e FORMAL_RUN=$ID/R001 -e SOURCE_COMMIT=$SHA \
  -e TRACKER_PROJECT=$ID -e TRACKER_RUN=R001 \
  exp-003:R001 --design /app/design.json --data-dir /data/food101 \
  --weights /data/weights/resnet18-f37072fd.pth --out /out
```

The image installs `runs/R001.requirements.txt` with hash checking on the base image pinned by digest in `Dockerfile`.
The run took 326 seconds on one RTX 5060 Ti. GPU training is not bit-for-bit deterministic, so a repeat should match
these numbers closely, not exactly. `design.json` can be regenerated with `make_design.py` (the arguments are the values
listed above; subset seed 0) and compared by content.
