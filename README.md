# Adaptive Privacy-Preserving Federated Learning for DDoS Detection
> *Adaptive Privacy-Preserving Federated Learning using FT-Transformer for Intelligent Real-Time DDoS Detection and Autonomous Multi-Stage Mitigation in Software-Defined Networks.*
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Overview

This system provides an end-to-end, privacy-preserving DDoS detection and mitigation framework. It trains an **FT-Transformer** model collaboratively across distributed network edge nodes using **Federated Learning (Flower)** — no raw traffic data ever leaves the edge. When a DDoS attack is detected, **SHAP** (Explainable AI) values inform an **Autonomous Mitigation Engine** that dynamically applies surgical OpenFlow rules via a **Ryu SDN Controller**.

### Key Properties
Property | Implementation 
**Privacy** | Local Differential Privacy (DP-SGD via Opacus)
**Robustness** | Adaptive Trust Scoring (Cosine Similarity)
**Explainability** | SHAP DeepExplainer on FT-Transformer
**Mitigation** | Multi-Stage SDN (Rate Limit → Isolate → Block)
**Network Sim** | Mininet + OpenVSwitch + Ryu Controller
## Architecture

Edge Nodes (FL Clients)          Trusted Core
┌─────────────────────┐          ┌──────────────────────────────────┐
│  FT-Transformer     │─gRPC────▶│  Flower Server (Aggregator)     │
│  Inference + SHAP   │          │  Adaptive Trust Scoring          │
│  Local DP-SGD       │          └──────────────────────────────────┘
└─────────────────────┘                     │ REST
         │ Alert + SHAP                     ▼
         ▼                        ┌──────────────────────────────────┐
┌─────────────────────┐          │  Mitigation Engine (FastAPI)     │
│  Mininet Topology   │◀─OpenFlow│  Decision Engine + Policy Engine │
│  OpenVSwitch        │          │  SDN Client + TTL Rollback       │
│  Ryu Controller     │          └──────────────────────────────────┘
└─────────────────────┘                     │ WebSocket/REST
                                            ▼
                                 ┌──────────────────────────────────┐
                                 │  React Dashboard (TypeScript)    │
                                 │  Live Alerts + SHAP Charts + FL  │
                                 └──────────────────────────────────┘
```
For full architectural details, see [`docs/Architecture.md`](docs/Architecture.md).
## Setup Guide (Step-by-Step)
This section walks you from a clean machine to a running Milestone 1 environment.
### Prerequisites
Install the following before starting:

Tool | Version | Download 
**Python** | 3.10+ | https://www.python.org/downloads/
**Git** | Latest | https://git-scm.com/downloads
**Docker Desktop** | Latest | https://www.docker.com/products/docker-desktop/
**Node.js** | 18+ | https://nodejs.org/ (for Dashboard, Milestone 32)

> **Windows users:** Use PowerShell or Git Bash. The shell scripts (`*.sh`) require Git Bash or WSL2.

### Step 1: Clone the Repository
```bash
git clone https://github.com/your-org/ddos-fl-system.git
cd ddos-fl-system
```
### Step 2: Create a Python Virtual Environment
**Linux / macOS / Git Bash (Windows):**
```bash
python3 -m venv .venv
source .venv/bin/activate
```
**Windows PowerShell:**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```
### Step 3: Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```
This installs: FastAPI, Flower (flwr), PyTorch, SHAP, SQLAlchemy, Alembic, Loguru, pytest, black, flake8, isort.
> **Note:** `torch` is a large download (~2 GB). Use a stable internet connection.
### Step 4: Configure Environment Variables

```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your values:
#   - DATABASE_URL (for local dev: postgresql://ddos_user:password@localhost:5432/ddos_db)
#   - JWT_SECRET_KEY (generate: openssl rand -hex 32)
```
### Step 5: Start the Database (Docker)
```bash
# Start only the PostgreSQL/TimescaleDB service
docker compose -f docker/docker-compose.yml up db -d
# Verify it is healthy
docker compose -f docker/docker-compose.yml ps
```
Expected output: `ddos_db ... (healthy)`
### Step 6: Run Database Migrations
```bash
# Apply the initial schema (creates all 9 tables from Database.md)
python scripts/init_db.py
```
Or directly with Alembic:
```bash
alembic upgrade head
```
### Step 7: Seed the Database (Optional)
```bash
# Inject mock data for dashboard testing
python scripts/seed_db.py
```
### Step 8: Verify the Setup
```bash
# Run unit tests — should all pass
pytest tests/unit/ -v
```
Expected output:
```
tests/unit/test_project_structure.py::... PASSED
tests/unit/test_shared_enums.py::... PASSED
tests/unit/test_shared_schemas.py::... PASSED
tests/unit/test_configs.py::... PASSED
```
## Running the System
### Core Services (Docker Compose)
```bash
# Start database + mitigation engine + FL server + dashboard
docker compose -f docker/docker-compose.yml up -d
# View logs
docker compose -f docker/docker-compose.yml logs -f
```
### Local Development (No Docker)
```bash
# Activate venv first
source .venv/bin/activate   # Linux/macOS
# or: .venv\Scripts\Activate.ps1  (PowerShell)
# Run all services locally (requires DB running)
chmod +x scripts/run_local.sh
./scripts/run_local.sh
```
### SDN Simulation (Linux/VM only)
```bash
# Requires Open vSwitch kernel module and Mininet installed
docker compose -f docker/docker-compose.mininet.yml up -d
```
---
## Running Tests

```bash
# Unit tests (no external dependencies)
pytest tests/unit/ -v

# Integration tests (requires running PostgreSQL)
pytest tests/integration/ -v -m integration

# System tests (requires full Docker stack)
pytest tests/system/ -v -m system

# Full test suite with coverage
pytest --cov=src --cov-report=html
open htmlcov/index.html
```
## License

MIT License. See [`LICENSE`](LICENSE) for details.
