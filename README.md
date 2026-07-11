# Adaptive Privacy-Preserving Federated Learning for DDoS Detection
> *Adaptive Privacy-Preserving Federated Learning using FT-Transformer for Intelligent Real-Time DDoS Detection and Autonomous Multi-Stage Mitigation in Software Defined Networks.*

[![CI Pipeline](https://github.com/your-org/ddos-fl-system/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/ddos-fl-system/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Setup Guide (Step-by-Step)](#setup-guide-step-by-step)
6. [Running the System](#running-the-system)
7. [Running Tests](#running-tests)
8. [Documentation](#documentation)
9. [Development Roadmap](#development-roadmap)
10. [Contributing](#contributing)
11. [License](#license)

---

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
For full architectural details see [`docs/Architecture.md`](docs/Architecture.md).
---

## Technology Stack
Layer | Technology
ML Model | FT-Transformer (PyTorch Tabular)
Federated Learning | Flower (flwr) 1.7.0
Explainability | SHAP 0.44.0
Backend | FastAPI 0.109 + Uvicorn 
Database | PostgreSQL 16 + TimescaleDB
SDN Controller | Ryu 4.34
Network Simulation | Mininet + OpenVSwitch
Frontend | React 18 + TypeScript + TailwindCSS
Containerization | Docker + Docker Compose

## Project Structure

├── docs/                    # All architectural documentation
│   ├── Architecture.md      # C4 diagrams, microservice design
│   ├── Database.md          # PostgreSQL/TimescaleDB schema
│   ├── API.md               # REST API specifications
│   ├── FederatedLearning.md # Flower FL architecture & trust scoring
│   ├── FTTransformer.md     # ML model architecture & SHAP
│   ├── Mitigation.md        # Autonomous mitigation engine design
│   ├── Dashboard.md         # React UI wireframes & routing
│   ├── Deployment.md        # Docker, environment, CI/CD
│   ├── DevelopmentRoadmap.md# 47 milestones with acceptance criteria
│   └── ProjectStructure.md  # Folder layout and responsibilities
├── src/
│   ├── fl_server/           # Flower federated learning server
│   ├── fl_client/           # Edge node: local training, inference, SHAP
│   ├── mitigation_engine/   # FastAPI: decision engine, SDN control, API
│   ├── sdn_controller/      # Ryu app, Mininet topology, flow extractor
│   ├── dashboard/           # React/TypeScript admin dashboard
│   └── shared/              # Shared Pydantic schemas, enums, logging
├── tests/
│   ├── unit/                # No external dependencies
│   ├── integration/         # Require running PostgreSQL
│   └── system/              # Require full Docker environment
├── notebooks/               # EDA, baseline training, SHAP analysis
├── scripts/                 # Env setup, dataset download, DB init
├── docker/                  # Dockerfiles + Docker Compose configs
├── alembic/                 # Database migration scripts
├── data/                    # Datasets (git-ignored)
└── .github/workflows/       # CI/CD pipelines

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

---

## Documentation

| Document | Description |
|---|---|
| [`docs/Research.md`](docs/Research.md) | Problem statement, gaps, methodology |
| [`docs/Architecture.md`](docs/Architecture.md) | C4 diagrams, microservice design |
| [`docs/Database.md`](docs/Database.md) | PostgreSQL/TimescaleDB schema |
| [`docs/API.md`](docs/API.md) | REST API specifications |
| [`docs/FederatedLearning.md`](docs/FederatedLearning.md) | Flower FL architecture |
| [`docs/FTTransformer.md`](docs/FTTransformer.md) | ML pipeline and SHAP integration |
| [`docs/Mitigation.md`](docs/Mitigation.md) | Autonomous mitigation engine |
| [`docs/Dashboard.md`](docs/Dashboard.md) | React UI design and wireframes |
| [`docs/Deployment.md`](docs/Deployment.md) | Docker, Kubernetes, CI/CD |
| [`docs/DevelopmentRoadmap.md`](docs/DevelopmentRoadmap.md) | 47 milestones with acceptance criteria |
| [`docs/ProjectStructure.md`](docs/ProjectStructure.md) | Folder layout and file responsibilities |

## Development Roadmap

The project is divided into 7 phases and 47 milestones. See [`docs/DevelopmentRoadmap.md`](docs/DevelopmentRoadmap.md) for full details.

| Phase | Milestones | Status |
|---|---|---|
| Phase 1: Research & Initialization | M1–M5 | P1 Complete |
| Phase 2: Data Engineering | M6–M12 |P2 Complete |
| Phase 3: Federated Learning | M13–M22 | P3 Complete |
| Phase 4: Mitigation Engine | M23–M31 | P4 Complete |
| Phase 5: Dashboard Frontend | M32–M37 | P5 Complete|
| Phase 6: SDN Simulation | M38–M42 | P6 Complete |
| Phase 7: Integration & Evaluation | M43–M47 | 🔲 Pending |

## License

MIT License. See [`LICENSE`](LICENSE) for details.
