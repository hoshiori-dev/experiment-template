"""Linear probe vs fine-tuning the last residual block of ResNet-18 on a Food-101 subset.

Read top to bottom: load the images the design names, push them once through the frozen part
of the network (conv1 .. layer3), then train each arm on those cached activations for every
learning rate and seed, pick the learning rate per arm on the tuning split, and only then
evaluate the test images at the picked learning rate.

Both arms share the frozen trunk, so caching its output changes nothing about either arm; it
only removes repeated work. There is no data augmentation, which is what makes the cache exact.

  probe     layer4 frozen (eval mode), only the new classifier is trained
  finetune  layer4 and the new classifier are trained
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import math
import os
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import torch
import torchvision
from PIL import Image
from torch import nn

IMAGE_SIZE = 224
RESIZE_TO = 256
NUM_CLASSES = 101
MEAN = (0.485, 0.456, 0.406)
STD = (0.229, 0.224, 0.225)


def decode(image_bytes: bytes) -> np.ndarray:
    """JPEG bytes to a centre-cropped uint8 array, channels first."""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    scale = RESIZE_TO / min(image.size)
    image = image.resize((round(image.width * scale), round(image.height * scale)), Image.BILINEAR)
    left = (image.width - IMAGE_SIZE) // 2
    top = (image.height - IMAGE_SIZE) // 2
    image = image.crop((left, top, left + IMAGE_SIZE, top + IMAGE_SIZE))
    return np.asarray(image, dtype=np.uint8).transpose(2, 0, 1)


def load_rows(data_dir: Path, split: str, rows: list[int]) -> tuple[torch.Tensor, torch.Tensor]:
    """Images and labels for the given row numbers of a split.

    A row number counts through the split's parquet files in file-name order; the pinned
    dataset revision makes that order immutable.
    """
    wanted = sorted(rows)
    position = 0
    encoded, labels = [], []
    for file in sorted((data_dir / "data").glob(f"{split}-*.parquet")):
        parquet = pq.ParquetFile(file)
        for group in range(parquet.num_row_groups):  # one row group at a time: the files are large
            size = parquet.metadata.row_group(group).num_rows
            local = [row - position for row in wanted if position <= row < position + size]
            if local:
                picked = parquet.read_row_group(group, columns=["image", "label"]).take(local)
                encoded += [item["bytes"] for item in picked.column("image").to_pylist()]
                labels += picked.column("label").to_pylist()
            position += size
    if len(encoded) != len(wanted):
        raise SystemExit(f"{split}: the design names {len(wanted)} rows, the data holds {len(encoded)} of them")
    with Pool() as pool:
        arrays = pool.map(decode, encoded, chunksize=64)
    return torch.from_numpy(np.stack(arrays)), torch.tensor(labels)


@torch.no_grad()
def trunk_activations(trunk: nn.Module, images: torch.Tensor, device: torch.device) -> torch.Tensor:
    """Output of the frozen trunk for uint8 images, kept on the device in half precision."""
    mean = torch.tensor(MEAN, device=device).view(1, 3, 1, 1)
    std = torch.tensor(STD, device=device).view(1, 3, 1, 1)
    out = []
    for start in range(0, len(images), 256):
        batch = images[start : start + 256].to(device).float().div(255)
        out.append(trunk((batch - mean) / std).half())
    return torch.cat(out)


@torch.no_grad()
def accuracy(head: nn.Module, activations: torch.Tensor, labels: torch.Tensor) -> float:
    head.eval()
    correct = 0
    for start in range(0, len(activations), 512):
        logits = head(activations[start : start + 512].float())
        correct += (logits.argmax(1) == labels[start : start + 512]).sum().item()
    return 100.0 * correct / len(labels)


def build_head(pretrained_layer4: nn.Module, seed: int) -> nn.Sequential:
    """layer4 with pretrained weights, pooling, and a freshly initialised classifier."""
    torch.manual_seed(seed)
    return nn.Sequential(
        copy.deepcopy(pretrained_layer4),
        nn.AdaptiveAvgPool2d(1),
        nn.Flatten(),
        nn.Linear(512, NUM_CLASSES),
    )


def train_head(head, arm, lr, seed, design, fit_x, fit_y, device, log) -> None:
    layer4, classifier = head[0], head[3]
    trained = classifier.parameters() if arm == "probe" else head.parameters()
    for parameter in layer4.parameters():
        parameter.requires_grad = arm == "finetune"
    optimizer = torch.optim.SGD(trained, lr=lr, momentum=0.9)
    steps_per_epoch = math.ceil(len(fit_x) / design["batch_size"])
    schedule = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, design["epochs"] * steps_per_epoch)
    order = torch.Generator(device="cpu").manual_seed(seed)
    for epoch in range(design["epochs"]):
        head.train()
        if arm == "probe":
            layer4.eval()  # frozen: batch-norm statistics stay at their pretrained values
        total = 0.0
        for index in torch.randperm(len(fit_x), generator=order).split(design["batch_size"]):
            index = index.to(device)
            loss = nn.functional.cross_entropy(head(fit_x[index].float()), fit_y[index])
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            schedule.step()
            total += loss.item() * len(index)
        log({f"{arm}/lr={lr:g}/seed={seed}/train_loss": total / len(fit_x)})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--design", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True, help="the Food-101 dataset at the declared revision")
    parser.add_argument("--weights", type=Path, required=True, help="the ImageNet ResNet-18 weight file")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--device", default="cuda", help="cuda or cpu; an unavailable device is an error")
    parser.add_argument("--skip-test", action="store_true", help="sizing: never load or evaluate a test image")
    args = parser.parse_args()

    design = json.loads(args.design.read_text())
    if args.device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("cuda was requested and is not available; not falling back to cpu")
    device = torch.device(args.device)
    args.out.mkdir(parents=True, exist_ok=True)

    import trackio  # imported here: it reads TRACKIO_DIR at import time

    formal_run = os.environ.get("FORMAL_RUN", "informal")
    trackio.init(
        project=os.environ.get("TRACKER_PROJECT", "exp-003-probe-vs-finetune-informal"),
        name=os.environ.get("TRACKER_RUN", "informal"),
        config={
            "formal_run": formal_run,
            "source_commit": os.environ.get("SOURCE_COMMIT", "none"),
            **design["protocol"],
        },
        auto_log_cpu=False,
        auto_log_gpu=False,
    )
    started = time.time()

    network = torchvision.models.resnet18(weights=None)
    network.load_state_dict(torch.load(args.weights, map_location="cpu", weights_only=True))
    trunk = nn.Sequential(
        network.conv1, network.bn1, network.relu, network.maxpool, network.layer1, network.layer2, network.layer3
    )
    trunk.eval().to(device)

    splits = ["fit", "tune"] if args.skip_test else ["fit", "tune", "test"]
    x, y = {}, {}
    for name in splits:
        source = "validation" if name == "test" else "train"
        images, labels = load_rows(args.data_dir, source, design["rows"][name])
        x[name] = trunk_activations(trunk, images, device)
        y[name] = labels.to(device)
        print(f"{name}: {len(labels)} images from the {source} split, {time.time() - started:.0f}s", flush=True)

    protocol = design["protocol"]
    tune_accuracy = {}  # (arm, lr, seed) -> accuracy on the tuning split
    heads = {}  # (arm, lr, seed) -> trained head, kept until the learning rate is selected
    for arm in protocol["arms"]:
        for lr in protocol["learning_rates"]:
            for seed in protocol["seeds"]:
                head = build_head(network.layer4, seed).to(device)
                train_head(head, arm, lr, seed, protocol, x["fit"], y["fit"], device, trackio.log)
                tune_accuracy[arm, lr, seed] = accuracy(head, x["tune"], y["tune"])
                heads[arm, lr, seed] = head.cpu()
                trackio.log({f"{arm}/lr={lr:g}/seed={seed}/tune_accuracy": tune_accuracy[arm, lr, seed]})
            mean = np.mean([tune_accuracy[arm, lr, seed] for seed in protocol["seeds"]])
            print(f"{arm} lr={lr:g}: tuning accuracy {mean:.2f}, {time.time() - started:.0f}s", flush=True)

    result = {"formal_run": formal_run, "design_sha256": os.environ.get("DESIGN_SHA256", "unknown"), "arms": {}}
    for arm in protocol["arms"]:
        mean_tune = {
            lr: float(np.mean([tune_accuracy[arm, lr, seed] for seed in protocol["seeds"]]))
            for lr in protocol["learning_rates"]
        }
        selected = max(mean_tune, key=mean_tune.get)
        entry = {
            "selected_learning_rate": selected,
            "mean_tune_accuracy": {f"{lr:g}": mean_tune[lr] for lr in mean_tune},
        }
        if not args.skip_test:
            test = [accuracy(heads[arm, selected, seed].to(device), x["test"], y["test"]) for seed in protocol["seeds"]]
            entry["test_accuracy_per_seed"] = test
            entry["test_accuracy_mean"] = float(np.mean(test))
            entry["test_accuracy_std"] = float(np.std(test, ddof=1))
            trackio.log({f"{arm}/test_accuracy_mean": entry["test_accuracy_mean"]})
            trackio.log({f"{arm}/test_accuracy_std": entry["test_accuracy_std"]})
        result["arms"][arm] = entry

    result["seconds"] = round(time.time() - started, 1)
    (args.out / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    trackio.log({"seconds": result["seconds"]})
    trackio.finish()
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
