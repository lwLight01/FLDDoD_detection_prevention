"""
tests/unit/test_shared_schemas.py
-----------------------------------
Unit tests for shared/schemas.py Pydantic models.

Acceptance Criteria (Milestone 1):
  - All schemas validate valid payloads without error.
  - All schemas reject invalid payloads with appropriate ValidationError.
  - Field constraints (probability bounds, non-empty SHAP) are enforced.
"""

import pytest
from datetime import datetime
from uuid import uuid4

from pydantic import ValidationError

from shared.schemas import (
    AlertCreate,
    AlertResponse,
    MitigationActionCreate,
    MitigationActionResponse,
    HealthResponse,
)
from shared.enums import MitigationLevel, MitigationStatus, SeverityLevel


CLIENT_UUID = uuid4()


class TestAlertCreate:
    def _valid_payload(self) -> dict:
        return {
            "client_id": str(CLIENT_UUID),
            "src_ip": "10.0.0.99",
            "prediction_probability": 0.97,
            "shap_values": {"tcp_flags_syn": 0.45, "flow_duration": 0.22},
        }

    def test_valid_payload_passes(self):
        alert = AlertCreate(**self._valid_payload())
        assert alert.prediction_probability == 0.97
        assert "tcp_flags_syn" in alert.shap_values

    def test_probability_above_1_rejected(self):
        payload = self._valid_payload()
        payload["prediction_probability"] = 1.5
        with pytest.raises(ValidationError):
            AlertCreate(**payload)

    def test_probability_below_0_rejected(self):
        payload = self._valid_payload()
        payload["prediction_probability"] = -0.1
        with pytest.raises(ValidationError):
            AlertCreate(**payload)

    def test_empty_shap_values_rejected(self):
        payload = self._valid_payload()
        payload["shap_values"] = {}
        with pytest.raises(ValidationError, match="shap_values must contain"):
            AlertCreate(**payload)

    def test_invalid_ip_rejected(self):
        payload = self._valid_payload()
        payload["src_ip"] = "not-an-ip"
        with pytest.raises(ValidationError):
            AlertCreate(**payload)

    def test_timestamp_defaults_to_utcnow(self):
        alert = AlertCreate(**self._valid_payload())
        assert isinstance(alert.timestamp, datetime)


class TestMitigationActionCreate:
    def test_valid_block_action(self):
        action = MitigationActionCreate(
            target_ip="192.168.1.5",
            action_type=MitigationLevel.QUARANTINE,
            duration_seconds=3600,
        )
        assert action.action_type == MitigationLevel.QUARANTINE

    def test_duration_below_minimum_rejected(self):
        with pytest.raises(ValidationError):
            MitigationActionCreate(
                target_ip="192.168.1.5",
                action_type=MitigationLevel.RATE_LIMIT,
                duration_seconds=30,   # minimum is 60
            )

    def test_duration_above_maximum_rejected(self):
        with pytest.raises(ValidationError):
            MitigationActionCreate(
                target_ip="192.168.1.5",
                action_type=MitigationLevel.RATE_LIMIT,
                duration_seconds=99999,  # maximum is 86400
            )


class TestHealthResponse:
    def test_valid_health_response(self):
        h = HealthResponse(
            status="healthy",
            database="connected",
            fl_server="reachable",
            ryu_controller="reachable",
        )
        assert h.status == "healthy"
