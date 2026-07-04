from __future__ import annotations
import io
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
import torch
@pytest.fixture()
def sample_df() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    n = 1000
    return pd.DataFrame(
        {
            "Flow Duration": rng.exponential(scale=1e6, size=n),
            "Total Fwd Packets": rng.integers(1, 1000, size=n).astype(float),
            "Total Bwd Packets": rng.integers(1, 500, size=n).astype(float),
            "Fwd Packet Length Max": rng.integers(64, 1500, size=n).astype(float),
            "Fwd Packet Length Min": rng.integers(40, 64, size=n).astype(float),
            "Fwd Packet Length Mean": rng.uniform(40, 1500, size=n),
            "Flow Bytes/s": rng.exponential(scale=1e5, size=n),
            "Flow Packets/s": rng.exponential(scale=1000, size=n),
            "Init_Win_bytes_forward": rng.integers(0, 65535, size=n).astype(float),
            "Active Mean": rng.exponential(scale=1e5, size=n),
            "Idle Mean": rng.exponential(scale=1e6, size=n),
            "Protocol": rng.choice([0, 6, 17], size=n),  
            "TCP Flags": rng.integers(0, 63, size=n),
            "Label": rng.integers(0, 2, size=n).astype(float),
        }
    )
@pytest.fixture()
def sample_csv(tmp_path: Path, sample_df: pd.DataFrame) -> Path:
    csv_path = tmp_path / "test_flows.csv"
    sample_df.to_csv(csv_path, index=False)
    return csv_path
class TestEncodeCategoricals:
    def test_tcp_protocol_mapped_to_1(self, sample_df: pd.DataFrame) -> None:
        from src.fl_client.dataset import encode_categoricals
        df = sample_df.copy()
        df["Protocol"] = 6  
        encoded = encode_categoricals(df)
        assert (encoded["Protocol"] == 1).all(), "TCP (6) should map to ordinal 1"
    def test_udp_protocol_mapped_to_2(self, sample_df: pd.DataFrame) -> None:
        from src.fl_client.dataset import encode_categoricals
        df = sample_df.copy()
        df["Protocol"] = 17  
        encoded = encode_categoricals(df)
        assert (encoded["Protocol"] == 2).all(), "UDP (17) should map to ordinal 2"
    def test_tcp_flags_clamped_to_0_63(self, sample_df: pd.DataFrame) -> None:
        from src.fl_client.dataset import encode_categoricals
        df = sample_df.copy()
        df["TCP Flags"] = 127  
        encoded = encode_categoricals(df)
        assert (encoded["TCP Flags"] == 63).all(), "Flags >63 should be clamped to 63"
    def test_unknown_protocol_mapped_to_unk(self, sample_df: pd.DataFrame) -> None:
        from src.fl_client.dataset import encode_categoricals
        df = sample_df.copy()
        df["Protocol"] = 99  
        encoded = encode_categoricals(df)
        assert (encoded["Protocol"] == 4).all(), "Unknown protocol should map to UNK (4)"
class TestQuantileTransformer:
    def test_mean_close_to_zero_after_normalization(self, sample_df: pd.DataFrame) -> None:
        from src.fl_client.dataset import fit_scaler, CONTINUOUS_FEATURES
        scaler = fit_scaler(sample_df, n_quantiles=500)
        transformed = scaler.transform(
            sample_df[CONTINUOUS_FEATURES].values.astype(np.float32)
        )
        means = np.mean(transformed, axis=0)
        assert np.allclose(means, 0.0, atol=0.5), (
            f"Means after normalization should be ≈ 0, got: {means}"
        )
    def test_scaler_serialization(self, tmp_path: Path, sample_df: pd.DataFrame) -> None:
        from src.fl_client.dataset import fit_scaler, save_scaler, load_scaler, CONTINUOUS_FEATURES
        scaler = fit_scaler(sample_df)
        save_scaler(scaler, tmp_path)
        loaded = load_scaler(tmp_path / "quantile_scaler.pkl")
        orig_out = scaler.transform(
            sample_df[CONTINUOUS_FEATURES].values[:5].astype(np.float32)
        )
        load_out = loaded.transform(
            sample_df[CONTINUOUS_FEATURES].values[:5].astype(np.float32)
        )
        np.testing.assert_array_almost_equal(orig_out, load_out, decimal=6)
class TestNetworkFlowDataset:
    def test_dataset_length(self, sample_csv: Path) -> None:
        from src.fl_client.dataset import NetworkFlowDataset
        ds = NetworkFlowDataset(sample_csv, fit_new_scaler=True)
        assert len(ds) == 1000
    def test_dataset_item_types(self, sample_csv: Path) -> None:
        from src.fl_client.dataset import NetworkFlowDataset
        ds = NetworkFlowDataset(sample_csv, fit_new_scaler=True)
        x_cont, x_cat, y = ds[0]
        assert isinstance(x_cont, torch.Tensor), "x_cont must be a Tensor"
        assert isinstance(x_cat, torch.Tensor), "x_cat must be a Tensor"
        assert isinstance(y, torch.Tensor), "y must be a Tensor"
    def test_dataset_item_shapes(self, sample_csv: Path) -> None:
        from src.fl_client.dataset import NetworkFlowDataset, CONTINUOUS_FEATURES, CATEGORICAL_FEATURES
        ds = NetworkFlowDataset(sample_csv, fit_new_scaler=True)
        x_cont, x_cat, y = ds[0]
        assert x_cont.shape == (len(CONTINUOUS_FEATURES),)
        assert x_cat.shape == (len(CATEGORICAL_FEATURES),)
        assert y.shape == ()
    def test_dataset_dtypes(self, sample_csv: Path) -> None:
        from src.fl_client.dataset import NetworkFlowDataset
        ds = NetworkFlowDataset(sample_csv, fit_new_scaler=True)
        x_cont, x_cat, y = ds[0]
        assert x_cont.dtype == torch.float32
        assert x_cat.dtype == torch.long
        assert y.dtype == torch.float32
    def test_file_not_found_raises(self, tmp_path: Path) -> None:
        from src.fl_client.dataset import NetworkFlowDataset
        with pytest.raises(FileNotFoundError):
            NetworkFlowDataset(tmp_path / "nonexistent.csv")
    def test_string_labels_binarized(self, tmp_path: Path, sample_df: pd.DataFrame) -> None:
        from src.fl_client.dataset import NetworkFlowDataset
        df = sample_df.copy()
        df["Label"] = np.where(df["Label"] == 0, "BENIGN", "DDoS-UDP")
        csv_path = tmp_path / "str_labels.csv"
        df.to_csv(csv_path, index=False)
        ds = NetworkFlowDataset(csv_path, fit_new_scaler=True)
        labels = ds.y.unique()
        assert set(labels.tolist()).issubset({0.0, 1.0}), "Labels must be binarized to 0/1"
class TestBuildDataloaders:
    def test_returns_three_elements(self, sample_csv: Path) -> None:
        from src.fl_client.dataset import build_dataloaders
        result = build_dataloaders(sample_csv, fit_new_scaler=True, batch_size=64)
        assert len(result) == 3, "build_dataloaders must return (train, val, scaler)"
    def test_batch_tensor_shapes(self, sample_csv: Path) -> None:
        from src.fl_client.dataset import build_dataloaders, CONTINUOUS_FEATURES, CATEGORICAL_FEATURES
        train_loader, _, _ = build_dataloaders(
            sample_csv, fit_new_scaler=True, batch_size=64
        )
        x_cont, x_cat, y = next(iter(train_loader))
        assert x_cont.shape[1] == len(CONTINUOUS_FEATURES)
        assert x_cat.shape[1] == len(CATEGORICAL_FEATURES)
        assert y.ndim == 1
    def test_train_val_split_sizes(self, sample_csv: Path) -> None:
        from src.fl_client.dataset import build_dataloaders
        train_loader, val_loader, _ = build_dataloaders(
            sample_csv, fit_new_scaler=True, batch_size=32, train_ratio=0.8
        )
        n_train = sum(len(y) for _, _, y in train_loader)
        n_val   = sum(len(y) for _, _, y in val_loader)
        assert abs((n_train + n_val) - 1000) <= 1  
    def test_no_nan_in_batches(self, sample_csv: Path) -> None:
        from src.fl_client.dataset import build_dataloaders
        train_loader, _, _ = build_dataloaders(
            sample_csv, fit_new_scaler=True, batch_size=64
        )
        for x_cont, x_cat, y in train_loader:
            assert not torch.isnan(x_cont).any(), "NaN in x_cont!"
            assert not torch.isnan(y).any(), "NaN in y!"
