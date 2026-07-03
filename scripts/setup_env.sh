#!/usr/bin/env bash
# ==============================================================================
# scripts/setup_env.sh
# ---------------------
# Initialises Python virtual environment and installs all project dependencies.
#
# Usage:
#   chmod +x scripts/setup_env.sh
#   ./scripts/setup_env.sh
#
# Acceptance Criteria (Milestone 3):
#   - Runs on a clean machine without errors.
#   - `pip install -r requirements.txt` succeeds.
#
# Ref: docs/DevelopmentRoadmap.md — Milestone 3
# ==============================================================================

set -euo pipefail

PYTHON=${PYTHON:-python3}
VENV_DIR="${VENV_DIR:-.venv}"

echo "=============================================="
echo " Adaptive FL DDoS System — Environment Setup"
echo "=============================================="

# ── 1. Check Python version ──────────────────────────────────────────────────
PYTHON_VERSION=$($PYTHON --version 2>&1 | awk '{print $2}')
REQUIRED_MAJOR=3
REQUIRED_MINOR=10

MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$MAJOR" -lt "$REQUIRED_MAJOR" ] || { [ "$MAJOR" -eq "$REQUIRED_MAJOR" ] && [ "$MINOR" -lt "$REQUIRED_MINOR" ]; }; then
    echo "ERROR: Python $REQUIRED_MAJOR.$REQUIRED_MINOR+ is required. Found: $PYTHON_VERSION" >&2
    exit 1
fi

echo "[OK] Python $PYTHON_VERSION detected."

# ── 2. Create virtual environment ────────────────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at ./$VENV_DIR ..."
    $PYTHON -m venv "$VENV_DIR"
    echo "[OK] Virtual environment created."
else
    echo "[OK] Virtual environment already exists at ./$VENV_DIR — skipping creation."
fi

# ── 3. Activate venv ─────────────────────────────────────────────────────────
# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"
echo "[OK] Virtual environment activated."

# ── 4. Upgrade pip ───────────────────────────────────────────────────────────
echo "Upgrading pip..."
pip install --upgrade pip --quiet
echo "[OK] pip upgraded."

# ── 5. Install global dependencies ───────────────────────────────────────────
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt --quiet
echo "[OK] All dependencies installed."

# ── 6. Create logs directory ─────────────────────────────────────────────────
mkdir -p logs
echo "[OK] logs/ directory ready."

# ── 7. Copy env template if .env doesn't exist ───────────────────────────────
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "[NOTICE] .env file created from .env.example. Edit it with your settings."
else
    echo "[OK] .env file already exists — not overwritten."
fi

echo ""
echo "=============================================="
echo " Setup complete!"
echo " Activate your environment with:"
echo "   source $VENV_DIR/bin/activate"
echo " Then run tests:"
echo "   pytest tests/unit/ -v"
echo "=============================================="
