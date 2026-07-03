# Project Folder Structure & Responsibilities

This document outlines the complete directory structure, file responsibilities, and configuration layout for the "Adaptive Privacy-Preserving Federated Learning using FT-Transformer for Intelligent DDoS Detection" project.

## Root Directory Structure

```text
/
├── docs/                   # Documentation (Architecture, Research, APIs, etc.)
├── data/                   # Raw and processed datasets (Ignored by Git)
├── src/                    # Source code for the entire system
│   ├── fl_server/          # Flower Server (Federated Aggregation)
│   ├── fl_client/          # Flower Client (Edge Node & FT-Transformer Inference)
│   ├── mitigation_engine/  # FastAPI backend for SDN control & Analytics
│   ├── sdn_controller/     # Ryu Controller scripts & Mininet topologies
│   ├── dashboard/          # React/TypeScript Frontend
│   └── shared/             # Shared Pydantic models, enums, & utilities
├── tests/                  # Unit, Integration, and System tests
├── notebooks/              # Jupyter notebooks for EDA and baseline modeling
├── scripts/                # Bash/Python scripts for deployment & data prep
├── docker/                 # Dockerfiles and Docker Compose configurations
├── .github/                # CI/CD workflows (GitHub Actions)
├── requirements.txt        # Python dependencies (Global/Reference)
├── .gitignore              # Git ignore file
└── README.md               # Main entry point and quickstart guide
```

---

## 1. Documentation (`/docs`)
*Purpose: Comprehensive project planning, architecture, and developer guides.*

*   `Architecture.md`: System context, C4 diagrams, and high-level design.
*   `Research.md`: Problem statement, gaps, methodology, and evaluation plan.
*   `ProjectStructure.md`: (This file) Folder layout and responsibilities.
*   `Database.md`: PostgreSQL schema, TimescaleDB setup, and ER diagrams.
*   `API.md`: REST API specifications for the Mitigation Engine.
*   `FederatedLearning.md`: Flower architecture, trust scoring, and aggregation logic.
*   `FTTransformer.md`: Model architecture, hyperparameters, and PyTorch setup.
*   `MitigationEngine.md`: SHAP integration and multi-stage rule logic.
*   `DevelopmentRoadmap.md`: Milestones and task breakdowns.

## 2. Research & Data (`/data` & `/notebooks`)
*Purpose: Data exploration, centralized baseline training, and dataset storage.*

### `/data`
*   `raw/`: Unprocessed PCAP files and raw CSVs (CIC-DDoS2019, etc.).
*   `processed/`: Cleaned, normalized tabular data ready for training.
*   `splits/`: Non-IID data distributions allocated for different FL clients.

### `/notebooks`
*   `01_eda_and_cleaning.ipynb`: Exploratory data analysis and feature engineering.
*   `02_centralized_baseline.ipynb`: Training centralized models (XGBoost, standard MLP).
*   `03_ft_transformer_tuning.ipynb`: Hyperparameter optimization for FT-Transformer using PyTorch Tabular.
*   `04_shap_analysis.ipynb`: Prototyping SHAP explanations on the trained tabular model.

## 3. Federated Learning Server (`/src/fl_server`)
*Purpose: Manages the global model, federated rounds, and adaptive trust scoring.*

*   `main.py`: Entry point; starts the Flower gRPC server.
*   `strategy.py`: Implements custom `flwr.server.strategy.Strategy` (Adaptive Trust Aggregation).
*   `trust_manager.py`: Calculates client trust scores based on gradient cosine similarity and historical behavior.
*   `dp_manager.py`: (Optional server-side) Adds global differential privacy noise.
*   `config.py`: Server configurations (num_rounds, min_clients).
*   `requirements.txt`: Specific dependencies (`flwr`, `torch`, `scipy`).

## 4. Federated Learning Client (`/src/fl_client`)
*Purpose: Runs on edge nodes, performs local training, model inference, and SHAP generation.*

*   `main.py`: Entry point; connects to FL server and starts local training loop.
*   `client.py`: Implements `flwr.client.NumPyClient` (fit, evaluate methods).
*   `model.py`: FT-Transformer model definition (via PyTorch Tabular or custom PyTorch implementation).
*   `dataset.py`: PyTorch DataLoader specifically for the local partition of tabular network flow data.
*   `inference.py`: Runs real-time inference on incoming flows and detects anomalies.
*   `xai_explainer.py`: Generates SHAP feature importance for positive DDoS predictions.
*   `alert_sender.py`: HTTP client that sends inference alerts and SHAP values to the Mitigation Engine.
*   `requirements.txt`: Dependencies (`flwr`, `torch`, `shap`, `pandas`).

## 5. Mitigation Engine & API (`/src/mitigation_engine`)
*Purpose: Translates AI alerts into SDN actions, logs data, and serves the dashboard.*

*   `main.py`: FastAPI application initialization and router inclusion.
*   `api/`
    *   `alerts.py`: Endpoints to receive alerts from `fl_client`.
    *   `metrics.py`: Endpoints to serve database metrics to the dashboard.
    *   `websocket.py`: WebSocket manager for real-time dashboard updates.
*   `services/`
    *   `analyzer.py`: Analyzes SHAP values to determine attack characteristics.
    *   `rule_generator.py`: Generates specific mitigation rules based on severity and XAI.
    *   `sdn_client.py`: Makes REST calls to the Ryu controller to install OpenFlow rules.
*   `db/`
    *   `database.py`: SQLAlchemy engine and session management.
    *   `models.py`: SQLAlchemy ORM models (Alerts, MitigationActions, TrustScores).
    *   `crud.py`: Database query functions.
*   `config.py`: Environment variables parsing (DB URI, Ryu URL).

## 6. SDN Controller & Simulation (`/src/sdn_controller`)
*Purpose: Network simulation and traffic control.*

*   `mininet_topo.py`: Mininet Python script defining the network topology (switches, hosts, attacker nodes).
*   `ryu_app.py`: Custom Ryu controller application handling OpenFlow 1.3.
*   `flow_extractor.py`: Ryu module that parses Packet-In messages and periodic flow stats into tabular format (CSV/Stream).
*   `mitigation_api.py`: Small REST server running *inside* or alongside Ryu to accept commands from the `mitigation_engine`.
*   `traffic_gen.sh`: Script to generate normal background traffic (iperf, curl).
*   `attack_gen.sh`: Script to launch simulated DDoS attacks (hping3, slowloris).

## 7. Admin Dashboard (`/src/dashboard`)
*Purpose: React-based UI for monitoring the system.*

*   `public/`: Static assets (index.html, icons).
*   `src/`
    *   `App.tsx`: Main React component and routing.
    *   `components/`: Reusable UI components (Cards, Navbar).
    *   `pages/`: Full views (Dashboard, FLStatus, XAIInsights, NetworkGraph).
    *   `hooks/`: Custom React hooks (`useWebSocket`, `useMetrics`).
    *   `services/`: Axios HTTP clients for the Mitigation Engine API.
*   `package.json`: Node dependencies (React, Recharts, TailwindCSS).
*   `tailwind.config.js`: Tailwind configuration.

## 8. Shared Utilities (`/src/shared`)
*Purpose: Code shared between multiple Python microservices to ensure consistency.*

*   `schemas.py`: Pydantic models for request/response validation (e.g., `AlertSchema`, `RuleSchema`).
*   `enums.py`: Global enumerations (e.g., `AttackType`, `MitigationLevel`).
*   `logger.py`: Standardized logging configuration for all Python modules.

## 9. Testing Structure (`/tests`)
*Purpose: Automated testing for CI/CD.*

*   `unit/`
    *   `test_fl_trust.py`: Tests for the adaptive trust scoring math.
    *   `test_rule_generator.py`: Tests that specific SHAP inputs yield correct mitigation rules.
    *   `test_model.py`: Validates FT-Transformer forward pass tensor shapes.
*   `integration/`
    *   `test_api_to_db.py`: Tests FastAPI writing to PostgreSQL.
    *   `test_engine_to_ryu.py`: Tests the API contract between the Mitigation Engine and Ryu.
*   `system/`
    *   `test_end_to_end.py`: Spins up minimal Docker environment and fires simulated alerts to verify full pipeline execution.

## 10. Docker & Deployment (`/docker`)
*Purpose: Containerization configurations.*

*   `docker-compose.yml`: Main compose file to spin up DB, FL Server, Mitigation Engine, API, and Dashboard.
*   `docker-compose.mininet.yml`: Separate compose file (requires privileged mode) for Mininet and Ryu.
*   `fl_server.Dockerfile`
*   `fl_client.Dockerfile`
*   `mitigation_engine.Dockerfile`
*   `dashboard.Dockerfile`
*   `ryu.Dockerfile`

## 11. Scripts (`/scripts`)
*Purpose: Helper tools for development and deployment.*

*   `setup_env.sh`: Initializes virtual environments and installs dependencies.
*   `download_datasets.sh`: Curl/Wget scripts to fetch public PCAP/CSV datasets.
*   `run_local.sh`: Runs microservices locally without Docker using screen or tmux.
*   `init_db.py`: SQLAlchemy script to create database tables.
*   `seed_db.py`: Injects mock data into the database for UI testing.
