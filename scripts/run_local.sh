#!/usr/bin/env bash
# ==============================================================================
# scripts/run_local.sh
# ----------------------
# Launches all microservices locally (without Docker) using background processes.
# Suitable for development iteration without Docker overhead.
#
# Usage:
#   chmod +x scripts/run_local.sh
#   ./scripts/run_local.sh
#
# Prerequisites:
#   - Virtual environment activated (.venv/bin/activate)
#   - PostgreSQL running locally with ddos_db created
#   - .env file configured
#
# Ref: docs/DevelopmentRoadmap.md — Milestone 3
#      docs/Deployment.md § 3 (Local Development)
# ==============================================================================

set -euo pipefail

LOG_DIR="logs"
mkdir -p "$LOG_DIR"

# Load environment variables from .env
if [ -f ".env" ]; then
    # shellcheck disable=SC2046
    export $(grep -v '^#' .env | xargs)
fi

echo "=============================================="
echo " Adaptive FL DDoS System — Local Run"
echo "=============================================="
echo " Logs → $LOG_DIR/"
echo ""

echo "[1/3] Starting Mitigation Engine (FastAPI)..."
# TODO (Milestone 23): Uncomment when mitigation_engine.main:app is implemented
# uvicorn mitigation_engine.main:app --host 0.0.0.0 --port 8000 --reload \
#     > "$LOG_DIR/mitigation_engine.log" 2>&1 &
# ME_PID=$!
# echo "      PID: $ME_PID | Port: 8000 | Log: $LOG_DIR/mitigation_engine.log"
echo "      [SKIP] Not yet implemented — Milestone 23"
echo ""

echo "[2/3] Starting Flower FL Server..."
# TODO (Milestone 13): Uncomment when fl_server.main is implemented
# python -m fl_server.main > "$LOG_DIR/fl_server.log" 2>&1 &
# FL_PID=$!
# echo "      PID: $FL_PID | Port: 8080 | Log: $LOG_DIR/fl_server.log"
echo "      [SKIP] Not yet implemented — Milestone 13"
echo ""

echo "[3/3] Starting React Dashboard dev server..."
# TODO (Milestone 32): Uncomment when dashboard is scaffolded
# cd src/dashboard && npm run dev > "../../$LOG_DIR/dashboard.log" 2>&1 &
# DASH_PID=$!
# cd ../..
# echo "      PID: $DASH_PID | Port: 5173 | Log: $LOG_DIR/dashboard.log"
echo "      [SKIP] Not yet implemented — Milestone 32"
echo ""

echo "=============================================="
echo " Services started (Milestones 13, 23, 32)"
echo " Press Ctrl+C to stop all services."
echo "=============================================="

# Keep alive to allow Ctrl+C
wait
