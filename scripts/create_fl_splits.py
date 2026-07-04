from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
def dirichlet_split(
    df: pd.DataFrame,
    n_clients: int,
    alpha: float,
    label_col: str = "Label",
    seed: int = 42,
) -> list[pd.DataFrame]:
    rng = np.random.default_rng(seed)
    clients: list[list[pd.DataFrame]] = [[] for _ in range(n_clients)]
    for cls_label in df[label_col].unique():
        cls_idx = df.index[df[label_col] == cls_label].tolist()
        rng.shuffle(cls_idx)
        proportions = rng.dirichlet(alpha=np.repeat(alpha, n_clients))
        splits = (proportions * len(cls_idx)).astype(int)
        splits[-1] = len(cls_idx) - splits[:-1].sum()
        ptr = 0
        for i, count in enumerate(splits):
            end = ptr + max(count, 0)
            clients[i].append(df.loc[cls_idx[ptr:end]])
            ptr = end
    return [pd.concat(shards).sample(frac=1, random_state=seed) for shards in clients]
def protocol_skew_split(
    df: pd.DataFrame,
    n_clients: int,
    seed: int = 42,
) -> list[pd.DataFrame]:
    rng = np.random.default_rng(seed)
    protocols = df["Protocol"].unique().tolist()
    partitions: list[pd.DataFrame] = []
    for i in range(n_clients):
        if i < len(protocols):
            dominant_proto = protocols[i]
            dominant = df[df["Protocol"] == dominant_proto]
            others = df[df["Protocol"] != dominant_proto]
            n_dominant = int(len(dominant) * 0.8)
            n_other = int(len(others) * 0.2 / max(n_clients - 1, 1))
            dominant_sample = dominant.sample(n=min(n_dominant, len(dominant)), random_state=seed + i)
            other_sample = others.sample(n=min(n_other, len(others)), random_state=seed + i)
            partition = pd.concat([dominant_sample, other_sample]).sample(frac=1, random_state=seed)
        else:
            partition = df.sample(frac=1 / n_clients, random_state=seed + i)
        partitions.append(partition)
    return partitions
def analyse_splits(partitions: list[pd.DataFrame], label_col: str = "Label") -> dict:
    report: dict = {"n_clients": len(partitions), "clients": []}
    for i, part in enumerate(partitions):
        total = len(part)
        dist = part[label_col].value_counts(normalize=True).to_dict()
        report["clients"].append(
            {
                "client_id": i,
                "n_samples": total,
                "label_distribution": {str(k): round(float(v), 4) for k, v in dist.items()},
            }
        )
    return report
def print_report(report: dict) -> None:
    print("\n" + "=" * 60)
    print(f"  Non-IID Split Report — {report['n_clients']} clients")
    print("=" * 60)
    for client in report["clients"]:
        dist_str = ", ".join(
            f"class {k}: {v:.1%}" for k, v in client["label_distribution"].items()
        )
        print(f"  Client {client['client_id']:>2}: {client['n_samples']:>7,} samples  |  {dist_str}")
    print("=" * 60 + "\n")
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Partition master CSV into Non-IID FL client splits."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/cicddos2019_processed.csv"),
        help="Path to the processed master CSV.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/splits"),
        help="Directory to write client partition CSVs.",
    )
    parser.add_argument(
        "--n-clients",
        type=int,
        default=5,
        metavar="N",
        help="Number of FL client partitions to generate. (default: 5)",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.5,
        help="Dirichlet concentration parameter. Lower = more non-IID. (default: 0.5)",
    )
    parser.add_argument(
        "--strategy",
        choices=["dirichlet", "protocol"],
        default="dirichlet",
        help="Splitting strategy: 'dirichlet' (default) or 'protocol'.",
    )
    parser.add_argument(
        "--label-col",
        default="Label",
        help="Target column name. (default: Label)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility. (default: 42)",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Optional path to save the JSON split report.",
    )
    return parser.parse_args(argv)
def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.input.exists():
        print(f"[ERROR] Input file not found: {args.input}", file=sys.stderr)
        return 1
    print(f"[INFO] Loading master dataset from: {args.input}")
    df = pd.read_csv(args.input, low_memory=False)
    print(f"[INFO] Loaded {len(df):,} samples with {len(df.columns)} columns.")
    if args.label_col not in df.columns:
        print(
            f"[ERROR] Label column '{args.label_col}' not found in {list(df.columns)}",
            file=sys.stderr,
        )
        return 1
    print(f"[INFO] Strategy: {args.strategy!r}  |  n_clients: {args.n_clients}  |  alpha: {args.alpha}")
    if args.strategy == "dirichlet":
        partitions = dirichlet_split(
            df, n_clients=args.n_clients, alpha=args.alpha,
            label_col=args.label_col, seed=args.seed,
        )
    else:
        partitions = protocol_skew_split(df, n_clients=args.n_clients, seed=args.seed)
    args.output.mkdir(parents=True, exist_ok=True)
    for i, part in enumerate(partitions):
        out_path = args.output / f"client_{i:02d}.csv"
        part.to_csv(out_path, index=False)
        print(f"[INFO] Saved client {i:02d}: {len(part):,} samples → {out_path}")
    report = analyse_splits(partitions, label_col=args.label_col)
    print_report(report)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with open(args.report, "w") as f:
            json.dump(report, f, indent=2)
        print(f"[INFO] Report saved to: {args.report}")
    return 0
if __name__ == "__main__":
    sys.exit(main())
