"""
tests/unit/test_milestone2_ci.py
----------------------------------
Unit tests for Milestone 2: Git Repository & CI Pipeline.

Validates that all CI/CD infrastructure files exist, are syntactically
valid, and contain the required configuration sections.

Acceptance Criteria (Milestone 2):
  - .gitignore correctly ignores sensitive and generated files.
  - .github/workflows/ci.yml is valid YAML and defines required jobs.
  - Project directory structure matches docs/ProjectStructure.md.

Ref: docs/DevelopmentRoadmap.md — Milestone 2
"""

import pytest
import yaml
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[2]


# ---------------------------------------------------------------------------
# .gitignore Tests
# ---------------------------------------------------------------------------

class TestGitignore:
    """Verify .gitignore correctly excludes sensitive and generated files."""

    def _get_gitignore_lines(self) -> list[str]:
        path = PROJECT_ROOT / ".gitignore"
        assert path.exists(), ".gitignore file must exist"
        return path.read_text(encoding="utf-8").splitlines()

    def test_gitignore_exists(self):
        assert (PROJECT_ROOT / ".gitignore").exists()

    def test_ignores_virtual_environment(self):
        lines = self._get_gitignore_lines()
        assert ".venv/" in lines, ".gitignore must exclude .venv/"

    def test_ignores_dot_env(self):
        lines = self._get_gitignore_lines()
        assert ".env" in lines, ".gitignore must exclude .env (secrets)"

    def test_ignores_pycache(self):
        lines = self._get_gitignore_lines()
        assert "__pycache__/" in lines

    def test_ignores_model_checkpoints(self):
        content = (PROJECT_ROOT / ".gitignore").read_text()
        assert "*.pt" in content or "checkpoints/" in content, \
            ".gitignore must exclude model checkpoint files"

    def test_ignores_raw_data(self):
        content = (PROJECT_ROOT / ".gitignore").read_text()
        assert "data/raw/*" in content, \
            ".gitignore must exclude raw data files (large datasets)"

    def test_ignores_certificates(self):
        content = (PROJECT_ROOT / ".gitignore").read_text()
        assert "*.pem" in content or "certs/" in content, \
            ".gitignore must exclude TLS certificates"

    def test_ignores_coverage_artifacts(self):
        content = (PROJECT_ROOT / ".gitignore").read_text()
        assert ".coverage" in content or "htmlcov/" in content, \
            ".gitignore must exclude test coverage artifacts"


# ---------------------------------------------------------------------------
# CI Workflow YAML Tests
# ---------------------------------------------------------------------------

class TestCIWorkflow:
    """Verify the GitHub Actions CI workflow is valid and complete."""

    def _load_ci_yaml(self) -> dict:
        ci_path = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
        assert ci_path.exists(), "ci.yml must exist at .github/workflows/ci.yml"
        with open(ci_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_ci_yml_exists(self):
        assert (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").exists()

    def test_ci_yml_is_valid_yaml(self):
        data = self._load_ci_yaml()
        assert isinstance(data, dict), "ci.yml must be a valid YAML mapping"

    def test_ci_triggers_on_push(self):
        data = self._load_ci_yaml()
        # PyYAML parses bare 'on:' key as Python True (YAML 1.1 bool)
        triggers = data.get(True, data.get("on", {}))
        assert "push" in triggers, \
            "CI must trigger on push events"

    def test_ci_triggers_on_pull_request(self):
        data = self._load_ci_yaml()
        triggers = data.get(True, data.get("on", {}))
        assert "pull_request" in triggers, \
            "CI must trigger on pull_request events"

    def test_ci_has_lint_and_test_job(self):
        data = self._load_ci_yaml()
        jobs = data.get("jobs", {})
        assert "lint-and-test" in jobs, \
            "CI must define a 'lint-and-test' job"

    def test_ci_has_docker_build_job(self):
        data = self._load_ci_yaml()
        jobs = data.get("jobs", {})
        assert "docker-build" in jobs, \
            "CI must define a 'docker-build' job"

    def test_ci_has_integration_tests_job(self):
        data = self._load_ci_yaml()
        jobs = data.get("jobs", {})
        assert "integration-tests" in jobs, \
            "CI must define an 'integration-tests' job"

    def test_lint_job_runs_black(self):
        data = self._load_ci_yaml()
        steps = data["jobs"]["lint-and-test"]["steps"]
        step_texts = [str(s) for s in steps]
        assert any("black" in s for s in step_texts), \
            "CI lint job must run black formatter check"

    def test_lint_job_runs_flake8(self):
        data = self._load_ci_yaml()
        steps = data["jobs"]["lint-and-test"]["steps"]
        step_texts = [str(s) for s in steps]
        assert any("flake8" in s for s in step_texts), \
            "CI lint job must run flake8 linter"

    def test_lint_job_runs_isort(self):
        data = self._load_ci_yaml()
        steps = data["jobs"]["lint-and-test"]["steps"]
        step_texts = [str(s) for s in steps]
        assert any("isort" in s for s in step_texts), \
            "CI lint job must run isort import order check"

    def test_lint_job_runs_pytest(self):
        data = self._load_ci_yaml()
        steps = data["jobs"]["lint-and-test"]["steps"]
        step_texts = [str(s) for s in steps]
        assert any("pytest" in s for s in step_texts), \
            "CI lint job must run pytest"

    def test_integration_job_has_postgres_service(self):
        data = self._load_ci_yaml()
        services = data["jobs"]["integration-tests"].get("services", {})
        assert "db" in services, \
            "Integration job must define a PostgreSQL service"
        assert "timescale" in services["db"]["image"], \
            "CI DB service must use TimescaleDB image"

    def test_branches_include_main_and_develop(self):
        data = self._load_ci_yaml()
        triggers = data.get(True, data.get("on", {}))
        push_branches = triggers.get("push", {}).get("branches", [])
        assert "main" in push_branches, "CI must trigger on 'main' branch"
        assert "develop" in push_branches, "CI must trigger on 'develop' branch"
