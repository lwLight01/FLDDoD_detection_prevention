"""
tests/integration/test_api_to_db.py
-------------------------------------
Integration tests: FastAPI alert endpoint writes correctly to PostgreSQL.
Requires a running PostgreSQL instance (see docker/docker-compose.yml).

Implementation deferred to Milestone 23/24.
Ref: docs/DevelopmentRoadmap.md — Milestone 23
"""
# TODO (Milestone 23): Implement integration tests using pytest-asyncio + TestClient
import pytest

@pytest.mark.skip(reason="Requires running DB — implement in Milestone 23")
def test_placeholder():
    pass
