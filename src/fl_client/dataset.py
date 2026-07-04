from __future__ import annotations
import pickle
from pathlib import Path
from typing import Optional, Tuple
import numpy as np
import pandas as pd
import torch
from sklearn.preprocessing import QuantileTransformer
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
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
CATEGORICAL_CARDINALITIES: dict[str, int] = {
    "Protocol": 5,   
    "TCP Flags": 65, 
}
SCALER_FILENAME = "quantile_scaler.pkl"
ENCODING_FILENAME = "categorical_encoders.pkl"
def fit_scaler(
    df: pd.DataFrame,
    n_quantiles: int = 1000,
    output_distribution: str = "normal",
    random_state: int = 42,
) -> QuantileTransformer:
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
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / SCALER_FILENAME, "wb") as f:
        pickle.dump(scaler, f)
def load_scaler(scaler_path: Path) -> QuantileTransformer:
    with open(scaler_path, "rb") as f:
        return pickle.load(f)
def encode_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    proto_map = {6: 1, 17: 2, 1: 3, 0: 0}
    df["Protocol"] = (
        df["Protocol"].map(proto_map).fillna(4).astype(np.int64)
    )
    if "TCP Flags" in df.columns:
        df["TCP Flags"] = (
            df["TCP Flags"]
            .clip(lower=0, upper=63)
            .fillna(64)
            .astype(np.int64)
        )
    else:
        df["TCP Flags"] = 0  
    return df
class NetworkFlowDataset(Dataset):
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
        cont_values = df[CONTINUOUS_FEATURES].values.astype(np.float32)
        if scaler is not None:
            self.scaler: Optional[QuantileTransformer] = scaler
            cont_values = scaler.transform(cont_values)
        elif fit_new_scaler:
            self.scaler = fit_scaler(df)
            cont_values = self.scaler.transform(cont_values)
        else:
            self.scaler = None  
        self.X_cont = torch.tensor(cont_values, dtype=torch.float32)
        cat_values = df[CATEGORICAL_FEATURES].values.astype(np.int64)
        self.X_cat = torch.tensor(cat_values, dtype=torch.long)
        labels = df[TARGET_COLUMN].values.astype(np.float32)
        self.y = torch.tensor(labels, dtype=torch.float32)
    @staticmethod
    def _clean(df: pd.DataFrame) -> pd.DataFrame:
        df.columns = df.columns.str.strip()
        df = df.replace([np.inf, -np.inf], np.nan)
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        df[num_cols] = df[num_cols].fillna(df[num_cols].median())
        if df[TARGET_COLUMN].dtype == object:
            df[TARGET_COLUMN] = (
                df[TARGET_COLUMN].str.upper().ne("BENIGN").astype(np.float32)
            )
        return df
    def __len__(self) -> int:
        return len(self.y)
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        return self.X_cont[idx], self.X_cat[idx], self.y[idx]
    @property
    def class_weights(self) -> torch.Tensor:
        n_samples = len(self.y)
        labels_np = self.y.numpy()
        n_pos = labels_np.sum()
        n_neg = n_samples - n_pos
        weight_pos = n_samples / (2.0 * n_pos) if n_pos > 0 else 1.0
        weight_neg = n_samples / (2.0 * n_neg) if n_neg > 0 else 1.0
        weights = np.where(labels_np == 1, weight_pos, weight_neg)
        return torch.tensor(weights, dtype=torch.float32)
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
    csv_path = Path(csv_path)
    full_dataset = NetworkFlowDataset(
        csv_path,
        scaler=scaler,
        fit_new_scaler=fit_new_scaler,
    )
    returned_scaler: Optional[QuantileTransformer] = (
        full_dataset.scaler if scaler is None else scaler
    )
    generator = torch.Generator().manual_seed(seed)
    n_total = len(full_dataset)
    n_train = int(n_total * train_ratio)
    n_val = n_total - n_train
    train_subset, val_subset = torch.utils.data.random_split(
        full_dataset, [n_train, n_val], generator=generator
    )
    if use_weighted_sampler and n_train > 0:
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
