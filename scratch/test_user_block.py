import sys
from pathlib import Path
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

PROJECT_ROOT = Path('.').resolve()
sys.path.insert(0, str(PROJECT_ROOT))

RAW_DIR = PROJECT_ROOT / 'data' / 'raw'
df_raw = pd.read_csv(RAW_DIR / 'cicddos2019_dataset.csv', low_memory=False)

SELECTED_FEATURES = [
    'Flow Duration', 'Total Fwd Packets', 'Total Backward Packets',
    'Fwd Packet Length Max', 'Fwd Packet Length Min', 'Fwd Packet Length Mean',
    'Flow Bytes/s', 'Flow Packets/s', 'Init_Win_bytes_forward',
    'Active Mean', 'Idle Mean', 'Protocol', 'TCP Flags', 'Label',
]
COLUMN_ALIASES = {
    'Total Backward Packets': 'Total Bwd Packets',
    ' Label': 'Label', 'label': 'Label', ' Protocol': 'Protocol',
    'Fwd PSH Flags': 'TCP Flags',
    'Init Fwd Win Bytes': 'Init_Win_bytes_forward',
}

df_raw.columns = df_raw.columns.str.strip()
df_raw = df_raw.rename(columns=COLUMN_ALIASES)
for col in SELECTED_FEATURES:
    if col not in df_raw.columns:
        df_raw[col] = 0
df = df_raw[SELECTED_FEATURES].copy()

# The pasted code block:
from src.fl_client.dataset import (
    encode_categoricals, fit_scaler, save_scaler, build_dataloaders, load_scaler,
    CONTINUOUS_FEATURES, CATEGORICAL_FEATURES, TARGET_COLUMN
)

df_clean = df.copy().replace([np.inf, -np.inf], np.nan)
df_clean = df_clean.rename(columns={'Total Backward Packets': 'Total Bwd Packets'})
num_cols = df_clean.select_dtypes(include=[np.number]).columns
df_clean[num_cols] = df_clean[num_cols].fillna(df_clean[num_cols].median())

df_encoded = encode_categoricals(df_clean)
if df_encoded[TARGET_COLUMN].dtype == object:
    df_encoded[TARGET_COLUMN] = df_encoded[TARGET_COLUMN].str.upper().ne('BENIGN').astype(int)

for col in CONTINUOUS_FEATURES:
    if col not in df_encoded.columns:
        df_encoded[col] = 0.0

scaler = fit_scaler(df_encoded)
df_encoded[CONTINUOUS_FEATURES] = scaler.transform(
    df_encoded[CONTINUOUS_FEATURES].values.astype(np.float32)
)

means = df_encoded[CONTINUOUS_FEATURES].mean()
print('Post-normalization mean:')
print(means.round(3))
assert (means.abs() < 0.5).all(), f'Means not close to 0! Means:\n{means}'
print('[M8] ✅ Normalization verified.')
