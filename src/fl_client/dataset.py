"""
fl_client/dataset.py
--------------------
PyTorch Dataset and DataLoader for tabular network flow data.

Responsibilities:
  - Load a local CSV partition (Non-IID split) into a PyTorch Dataset.
  - Apply preprocessing transformations consistently with the global
    normalization parameters (frozen QuantileTransformer state from the
    centralized training phase).
  - Handle class imbalance via WeightedRandomSampler.

Data Schema (CIC-DDoS2019 features, ref: docs/FTTransformer.md § 1.1):
  Continuous: Flow Duration, Total Fwd Packets, Total Bwd Packets,
              Fwd Packet Length Max/Min/Mean, Flow Bytes/s, Flow Packets/s,
              Init_Win_bytes_forward, Active Mean, Idle Mean
  Categorical: Protocol, TCP Flags (encoded as ordinal)
  Target:     Label (0=Benign, 1=DDoS)

Ref: docs/FTTransformer.md § 1, docs/DevelopmentRoadmap.md — Milestone 8
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd
import torch
from sklearn.preprocessing import QuantileTransformer
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler

# ---------------------------------------------------------------------------
# Feature schema — keep in sync with docs/FTTransformer.md § 1.1
# ---------------------------------------------------------------------------

CONTINUOUS_FEATURES: list[str] = [
    "Flow Duration",
    "Total Fwd Packets",
    "Total Bwd Packets",
    "Fwd Packet Length Max",
    "Fwd Packet Length Min",
    "Fwd Packet Length Mean",
    "Flow Bytes/s",
    "Flow Packets/s",
    "Init_Win_bytes_forward",
    "Active Mean",
    "Idle Mean",
]

CATEGORICAL_FEATURES: list[str] = [
    "Protocol",
    "TCP Flags",
]

TARGET_COLUMN: str = "Label"

# Cardinality of each categorical feature (max ordinal value + 1).
# Values exceeding these bounds are mapped to the [UNK] index (cardinality - 1).
CATEGORICAL_CARDINALITIES: dict[str, int] = {
    "Protocol": 5,   # 0=HOPOPT,1=TCP,2=UDP,3=ICMP,4=UNK
    "TCP Flags": 65, # 0-63 for 6-bit flag combinations, 64=UNK
}

SCALER_FILENAME = "quantile_scaler.pkl"
ENCODING_FILENAME = "categorical_encoders.pkl"


# ---------------------------------------------------------------------------
# Preprocessing utilities
# ---------------------------------------------------------------------------


def fit_scaler(
    df: pd.DataFrame,
    n_quantiles: int = 1000,
    output_distribution: str = "normal",
    random_state: int = 42,
) -> QuantileTransformer:
    """Fit a QuantileTransformer on the continuous features of *df*.

    Args:
        df: DataFrame containing at least the CONTINUOUS_FEATURES columns.
        n_quantiles: Number of quantiles to compute (capped at sample count).
        output_distribution: ``"normal"`` or ``"uniform"``.
        random_state: Reproducibility seed.

    Returns:
        A fitted ``QuantileTransformer`` instance.
    """
    n_quantiles = min(n_quantiles, len(df))
    qt = QuantileTransformer(
        n_quantiles=n_quantiles,
        output_distribution=output_distribution,
        random_state=random_state,
        subsample=200_000,
    )
    qt.fit(df[CONTINUOUS_FEATURES].values.astype(np.float32))
    return qt


def save_scaler(scaler: QuantileTransformer, output_dir: Path) -> None:
    """Persist *scaler* to *output_dir* as a pickle file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / SCALER_FILENAME, "wb") as f:
        pickle.dump(scaler, f)


def load_scaler(scaler_path: Path) -> QuantileTransformer:
    """Load a previously serialized QuantileTransformer."""
    with open(scaler_path, "rb") as f:
        return pickle.load(f)


def encode_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """Map raw categorical values to ordinal integers in-place.

    Unknown values are mapped to the ``[UNK]`` index (cardinality - 1).

    Protocol mapping: TCP=6→1, UDP=17→2, ICMP=1→3, others→0 or UNK.
    TCP Flags: raw integer bitmask clamped to [0, 63]; 64=UNK.
    """
    df = df.copy()

    # Protocol
    proto_map = {6: 1, 17: 2, 1: 3, 0: 0}
    df["Protocol"] = (
        df["Protocol"].map(proto_map).fillna(4).astype(np.int64)
    )

    # TCP Flags — raw int bitmask [0, 63]
    if "TCP Flags" in df.columns:
        df["TCP Flags"] = (
            df["TCP Flags"]
            .clip(lower=0, upper=63)
            .fillna(64)
            .astype(np.int64)
        )
    else:
        df["TCP Flags"] = 0  # Placeholder if column absent

    return df


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------


class NetworkFlowDataset(Dataset):
    """PyTorch Dataset wrapping a pre-processed network flow CSV.

    Args:
        csv_path: Path to a CSV file containing network flow features and labels.
        scaler: A fitted ``QuantileTransformer``. If ``None``, a new one is fit
            on this CSV (use only for the centralised training set).
        fit_new_scaler: When ``True`` and *scaler* is ``None``, fit a scaler
            on this dataset and expose it via ``self.scaler``.
    """

    def __init__(
        self,
        csv_path: Path,
        scaler: Optional[QuantileTransformer] = None,
        fit_new_scaler: bool = False,
    ) -> None:
        super().__init__()
        csv_path = Path(csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"Dataset CSV not found: {csv_path}")

        df = pd.read_csv(csv_path, low_memory=False)
        df = self._clean(df)
        df = encode_categoricals(df)

        # ── Continuous features ──
        cont_values = df[CONTINUOUS_FEATURES].values.astype(np.float32)

        if scaler is not None:
            self.scaler: Optional[QuantileTransformer] = scaler
            cont_values = scaler.transform(cont_values)
        elif fit_new_scaler:
            self.scaler = fit_scaler(df)
            cont_values = self.scaler.transform(cont_values)
        else:
            self.scaler = None  # Raw values — caller must normalise later

        self.X_cont = torch.tensor(cont_values, dtype=torch.float32)

        # ── Categorical features ──
        cat_values = df[CATEGORICAL_FEATURES].values.astype(np.int64)
        self.X_cat = torch.tensor(cat_values, dtype=torch.long)

        # ── Labels ──
        labels = df[TARGET_COLUMN].values.astype(np.float32)
        self.y = torch.tensor(labels, dtype=torch.float32)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _clean(df: pd.DataFrame) -> pd.DataFrame:
        """Standardise column names and coerce types."""
        df.columns = df.columns.str.strip()
        # Drop infinite values
        df = df.replace([np.inf, -np.inf], np.nan)
        # Fill numeric NaNs with column median
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        df[num_cols] = df[num_cols].fillna(df[num_cols].median())
        # Binarise labels: 0 for "BENIGN" / 0, 1 for everything else
        if df[TARGET_COLUMN].dtype == object:
            df[TARGET_COLUMN] = (
                df[TARGET_COLUMN].str.upper().ne("BENIGN").astype(np.float32)
            )
        return df

    # ------------------------------------------------------------------
    # Dataset protocol
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self.y)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Return ``(X_cont, X_cat, y)`` for a single sample."""
        return self.X_cont[idx], self.X_cat[idx], self.y[idx]

    @property
    def class_weights(self) -> torch.Tensor:
        """Per-sample weights suitable for ``WeightedRandomSampler``."""
        n_samples = len(self.y)
        labels_np = self.y.numpy()
        n_pos = labels_np.sum()
        n_neg = n_samples - n_pos
        weight_pos = n_samples / (2.0 * n_pos) if n_pos > 0 else 1.0
        weight_neg = n_samples / (2.0 * n_neg) if n_neg > 0 else 1.0
        weights = np.where(labels_np == 1, weight_pos, weight_neg)
        return torch.tensor(weights, dtype=torch.float32)


# ---------------------------------------------------------------------------
# DataLoader factory
# ---------------------------------------------------------------------------


def build_dataloaders(
    csv_path: Path,
    scaler: Optional[QuantileTransformer] = None,
    train_ratio: float = 0.8,
    batch_size: int = 256,
    num_workers: int = 0,
    seed: int = 42,
    fit_new_scaler: bool = False,
    use_weighted_sampler: bool = True,
) -> Tuple[DataLoader, DataLoader, Optional[QuantileTransformer]]:
    """Build train and validation DataLoaders from a single CSV file.

    Args:
        csv_path: Path to the CSV file.
        scaler: Pre-fitted QuantileTransformer (e.g., frozen global scaler).
            If ``None`` and *fit_new_scaler* is ``True``, a new scaler is
            fitted on the training split.
        train_ratio: Fraction of data used for training (remainder → validation).
        batch_size: Mini-batch size.
        num_workers: DataLoader worker processes (0 = main process only).
        seed: Random seed for the train/val split.
        fit_new_scaler: Whether to fit a new QuantileTransformer if *scaler*
            is not provided.
        use_weighted_sampler: If ``True``, apply ``WeightedRandomSampler`` on
            the training loader to handle class imbalance.

    Returns:
        Tuple of ``(train_loader, val_loader, scaler)``.  The returned *scaler*
        may be ``None`` if neither *scaler* was provided nor *fit_new_scaler*
        was requested.
    """
    csv_path = Path(csv_path)
    full_dataset = NetworkFlowDataset(
        csv_path,
        scaler=scaler,
        fit_new_scaler=fit_new_scaler,
    )
    returned_scaler: Optional[QuantileTransformer] = (
        full_dataset.scaler if scaler is None else scaler
    )

    # Deterministic split
    generator = torch.Generator().manual_seed(seed)
    n_total = len(full_dataset)
    n_train = int(n_total * train_ratio)
    n_val = n_total - n_train
    train_subset, val_subset = torch.utils.data.random_split(
        full_dataset, [n_train, n_val], generator=generator
    )

    # Sampler for class imbalance on training set
    if use_weighted_sampler and n_train > 0:
        # Extract per-sample weights for the training indices
        all_weights = full_dataset.class_weights
        train_weights = all_weights[train_subset.indices]
        sampler = WeightedRandomSampler(
            weights=train_weights,
            num_samples=len(train_weights),
            replacement=True,
            generator=generator,
        )
        train_loader = DataLoader(
            train_subset,
            batch_size=batch_size,
            sampler=sampler,
            num_workers=num_workers,
            pin_memory=torch.cuda.is_available(),
        )
    else:
        train_loader = DataLoader(
            train_subset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=num_workers,
            pin_memory=torch.cuda.is_available(),
        )

    val_loader = DataLoader(
        val_subset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
    )

    return train_loader, val_loader, returned_scaler
