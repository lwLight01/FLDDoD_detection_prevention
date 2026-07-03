"""
tests/unit/test_project_structure.py
--------------------------------------
Structural tests verifying the folder layout matches docs/ProjectStructure.md.

Acceptance Criteria (Milestone 1):
  - Every documented directory exists.
  - Every documented stub file exists.
  - All Python packages have __init__.py.
"""

import os
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]  # d:/Uni_Project/ML


REQUIRED_DIRS = [
    "docs",
    "data/raw",
    "data/processed",
    "data/splits",
    "src/fl_server",
    "src/fl_client",
    "src/mitigation_engine/api",
    "src/mitigation_engine/services",
    "src/mitigation_engine/db",
    "src/sdn_controller",
    "src/shared",
    "src/dashboard/src",
    "src/dashboard/public",
    "tests/unit",
    "tests/integration",
    "tests/system",
    "notebooks",
    "scripts",
    "docker",
    ".github/workflows",
    "alembic",
    "alembic/versions",
]

REQUIRED_FILES = [
    "README.md",
    "LICENSE",
    ".gitignore",
    ".env.example",
    "requirements.txt",
    "alembic.ini",
    ".github/workflows/ci.yml",
    # Shared
    "src/shared/__init__.py",
    "src/shared/enums.py",
    "src/shared/schemas.py",
    "src/shared/logger.py",
    # FL Server
    "src/fl_server/__init__.py",
    "src/fl_server/config.py",
    "src/fl_server/main.py",
    "src/fl_server/strategy.py",
    "src/fl_server/trust_manager.py",
    "src/fl_server/dp_manager.py",
    "src/fl_server/requirements.txt",
    # FL Client
    "src/fl_client/__init__.py",
    "src/fl_client/main.py",
    "src/fl_client/model.py",
    "src/fl_client/dataset.py",
    "src/fl_client/client.py",
    "src/fl_client/inference.py",
    "src/fl_client/xai_explainer.py",
    "src/fl_client/alert_sender.py",
    "src/fl_client/requirements.txt",
    # Mitigation Engine
    "src/mitigation_engine/__init__.py",
    "src/mitigation_engine/config.py",
    "src/mitigation_engine/main.py",
    "src/mitigation_engine/requirements.txt",
    "src/mitigation_engine/api/__init__.py",
    "src/mitigation_engine/api/alerts.py",
    "src/mitigation_engine/api/metrics.py",
    "src/mitigation_engine/api/websocket.py",
    "src/mitigation_engine/services/__init__.py",
    "src/mitigation_engine/services/analyzer.py",
    "src/mitigation_engine/services/rule_generator.py",
    "src/mitigation_engine/services/sdn_client.py",
    "src/mitigation_engine/db/__init__.py",
    "src/mitigation_engine/db/database.py",
    "src/mitigation_engine/db/models.py",
    "src/mitigation_engine/db/crud.py",
    # SDN
    "src/sdn_controller/__init__.py",
    "src/sdn_controller/ryu_app.py",
    "src/sdn_controller/mininet_topo.py",
    "src/sdn_controller/flow_extractor.py",
    "src/sdn_controller/mitigation_api.py",
    # Docker
    "docker/docker-compose.yml",
    "docker/docker-compose.mininet.yml",
    "docker/fl_server.Dockerfile",
    "docker/fl_client.Dockerfile",
    "docker/mitigation_engine.Dockerfile",
    "docker/dashboard.Dockerfile",
    "docker/ryu.Dockerfile",
    "docker/nginx.conf",
    # Scripts
    "scripts/setup_env.sh",
    "scripts/download_datasets.sh",
    "scripts/run_local.sh",
    "scripts/init_db.py",
    "scripts/seed_db.py",
    # Alembic
    "alembic/env.py",
    "alembic/script.py.mako",
    # Notebooks
    "notebooks/01_eda_and_cleaning.ipynb",
    "notebooks/02_centralized_baseline.ipynb",
    "notebooks/03_ft_transformer_tuning.ipynb",
    "notebooks/04_shap_analysis.ipynb",
    # Dashboard
    "src/dashboard/package.json",
    "src/dashboard/public/index.html",
    "src/dashboard/src/main.tsx",
    # Docs
    "docs/Research.md",
    "docs/Architecture.md",
    "docs/ProjectStructure.md",
    "docs/Database.md",
    "docs/API.md",
    "docs/FederatedLearning.md",
    "docs/FTTransformer.md",
    "docs/Mitigation.md",
    "docs/Dashboard.md",
    "docs/Deployment.md",
    "docs/DevelopmentRoadmap.md",
]


@pytest.mark.parametrize("directory", REQUIRED_DIRS)
def test_required_directory_exists(directory: str):
    path = ROOT / directory
    assert path.is_dir(), f"Missing required directory: {directory}"


@pytest.mark.parametrize("filepath", REQUIRED_FILES)
def test_required_file_exists(filepath: str):
    path = ROOT / filepath
    assert path.is_file(), f"Missing required file: {filepath}"


@pytest.mark.parametrize("pkg", [
    "src/shared",
    "src/fl_server",
    "src/fl_client",
    "src/mitigation_engine",
    "src/mitigation_engine/api",
    "src/mitigation_engine/services",
    "src/mitigation_engine/db",
    "src/sdn_controller",
])
def test_python_package_has_init(pkg: str):
    init = ROOT / pkg / "__init__.py"
    assert init.is_file(), f"Python package {pkg} is missing __init__.py"
