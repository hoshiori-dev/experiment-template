"""Write the design file: which images form the fit, tuning and test sets, and the protocol.

The subset is class-balanced: for every class, rows are drawn without replacement by a seeded
generator from the pinned dataset revision. Row numbers count through a split's parquet files
in file-name order. Reads only labels; no image is decoded and nothing is evaluated.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq


def labels_of(data_dir: Path, split: str) -> np.ndarray:
    files = sorted((data_dir / "data").glob(f"{split}-*.parquet"))
    return np.concatenate([pq.read_table(file, columns=["label"]).column("label").to_numpy() for file in files])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--fit-per-class", type=int, required=True)
    parser.add_argument("--tune-per-class", type=int, required=True)
    parser.add_argument("--test-per-class", type=int, required=True)
    parser.add_argument("--epochs", type=int, required=True)
    parser.add_argument("--batch-size", type=int, required=True)
    parser.add_argument("--learning-rates", type=float, nargs="+", required=True)
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    parser.add_argument("--subset-seed", type=int, default=0)
    args = parser.parse_args()

    generator = np.random.default_rng(args.subset_seed)
    train_labels = labels_of(args.data_dir, "train")
    test_labels = labels_of(args.data_dir, "validation")
    rows = {"fit": [], "tune": [], "test": []}
    for label in range(101):
        train_rows = generator.permutation(np.flatnonzero(train_labels == label))
        rows["fit"] += train_rows[: args.fit_per_class].tolist()
        rows["tune"] += train_rows[args.fit_per_class : args.fit_per_class + args.tune_per_class].tolist()
        rows["test"] += generator.permutation(np.flatnonzero(test_labels == label))[: args.test_per_class].tolist()
    assert not set(rows["fit"]) & set(rows["tune"]), "tuning rows must be held out from the fit rows"

    design = {
        "dataset": "ethz/food101",
        "subset_seed": args.subset_seed,
        "per_class": {"fit": args.fit_per_class, "tune": args.tune_per_class, "test": args.test_per_class},
        "protocol": {
            "arms": ["probe", "finetune"],
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "learning_rates": args.learning_rates,
            "seeds": args.seeds,
            "optimizer": "sgd, momentum 0.9, cosine schedule to zero, no weight decay",
            "input": "resize shorter side to 256, centre crop 224, no augmentation",
        },
        "rows": {name: sorted(values) for name, values in rows.items()},
    }
    args.out.write_text(json.dumps(design, separators=(",", ":")) + "\n")
    print({name: len(values) for name, values in rows.items()})


if __name__ == "__main__":
    main()
