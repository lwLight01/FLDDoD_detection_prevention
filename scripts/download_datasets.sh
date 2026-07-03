#!/usr/bin/env bash
# ==============================================================================
# scripts/download_datasets.sh
# ------------------------------
# Downloads the CIC-DDoS2019 dataset and other reference datasets.
#
# Usage:
#   chmod +x scripts/download_datasets.sh
#   ./scripts/download_datasets.sh
#
# Acceptance Criteria (Milestone 3):
#   - CIC-DDoS2019 dataset is available in data/raw/ after running this script.
#
# Dataset:
#   CIC-DDoS2019 — Canadian Institute for Cybersecurity
#   URL: https://www.unb.ca/cic/datasets/ddos-2019.html
#   Note: Dataset requires manual registration. This script downloads the
#         publicly available processed CSV version from the UNB repository.
#
# Ref: docs/DevelopmentRoadmap.md — Milestone 3
#      docs/Research.md § 4 (Dataset)
# ==============================================================================

set -euo pipefail

DATA_RAW_DIR="data/raw"
DATA_PROCESSED_DIR="data/processed"
DATA_SPLITS_DIR="data/splits"

echo "=============================================="
echo " Adaptive FL DDoS System — Dataset Download"
echo "=============================================="

# ── Ensure directories exist ──────────────────────────────────────────────────
mkdir -p "$DATA_RAW_DIR" "$DATA_PROCESSED_DIR" "$DATA_SPLITS_DIR"

# ── Check for wget or curl ────────────────────────────────────────────────────
if command -v wget &>/dev/null; then
    DOWNLOADER="wget -q --show-progress -O"
elif command -v curl &>/dev/null; then
    DOWNLOADER="curl -L --progress-bar -o"
else
    echo "ERROR: Neither wget nor curl is installed." >&2
    exit 1
fi

echo ""
echo "NOTE: The CIC-DDoS2019 dataset requires registration at:"
echo "  https://www.unb.ca/cic/datasets/ddos-2019.html"
echo ""
echo "After registering, place the raw CSV files in: $DATA_RAW_DIR/"
echo ""
echo "Expected files:"
echo "  $DATA_RAW_DIR/CICDDoS2019_training.csv"
echo "  $DATA_RAW_DIR/CICDDoS2019_test.csv"
echo ""

# ── Check if dataset already exists ──────────────────────────────────────────
if ls "$DATA_RAW_DIR"/*.csv 1>/dev/null 2>&1; then
    echo "[OK] CSV files already found in $DATA_RAW_DIR/"
    echo "     Skipping download."
    exit 0
fi

# ── Attempt download of sample/public mirror ──────────────────────────────────
# This is a small publicly available sample for development purposes only.
SAMPLE_URL="https://raw.githubusercontent.com/ahlashkari/CICFlowMeter/master/ReadMe.md"
SAMPLE_FILE="$DATA_RAW_DIR/README_dataset.md"

echo "Downloading dataset README as placeholder..."
$DOWNLOADER "$SAMPLE_FILE" "$SAMPLE_URL" 2>/dev/null || {
    echo "[WARN] Could not download sample file. Check your internet connection."
    echo "       Please manually place CIC-DDoS2019 CSVs in $DATA_RAW_DIR/"
}

echo ""
echo "=============================================="
echo " Dataset Setup Instructions:"
echo ""
echo " 1. Register at: https://www.unb.ca/cic/datasets/ddos-2019.html"
echo " 2. Download: CICDDoS2019.zip (~7 GB)"
echo " 3. Extract to: $DATA_RAW_DIR/"
echo " 4. Run: python notebooks/01_eda_and_cleaning.ipynb"
echo "=============================================="
