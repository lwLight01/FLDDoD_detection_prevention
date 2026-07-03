"""
tests/unit/test_shared_enums.py
--------------------------------
Unit tests for shared/enums.py.

Acceptance Criteria (Milestone 1):
  - All enum classes are importable.
  - All expected members exist with correct string values.
  - Enums are properly typed (str + Enum) for JSON serialisation.
"""

import pytest
from shared.enums import (
    AttackType,
    MitigationLevel,
    MitigationStatus,
    SeverityLevel,
    UserRole,
)


class TestAttackType:
    def test_all_members_exist(self):
        expected = {"BENIGN", "UDP_FLOOD", "SYN_FLOOD", "HTTP_FLOOD", "DNS_AMPLIFICATION", "UNKNOWN"}
        actual = {m.value for m in AttackType}
        assert expected == actual

    def test_is_string_serialisable(self):
        assert AttackType.SYN_FLOOD == "SYN_FLOOD"
        assert isinstance(AttackType.SYN_FLOOD, str)


class TestMitigationLevel:
    def test_stages_ordered(self):
        """Stages must exist and be distinct for the Policy Engine stage mapping."""
        assert MitigationLevel.NONE != MitigationLevel.RATE_LIMIT
        assert MitigationLevel.RATE_LIMIT != MitigationLevel.ISOLATE
        assert MitigationLevel.ISOLATE != MitigationLevel.QUARANTINE

    def test_string_values(self):
        assert MitigationLevel.RATE_LIMIT == "RATE_LIMIT"
        assert MitigationLevel.QUARANTINE == "QUARANTINE"


class TestMitigationStatus:
    def test_all_lifecycle_states_exist(self):
        expected = {"PENDING", "SUCCESS", "FAILED", "REVOKED"}
        actual = {m.value for m in MitigationStatus}
        assert expected == actual


class TestUserRole:
    def test_all_roles_exist(self):
        expected = {"ADMIN", "ANALYST", "READONLY"}
        actual = {m.value for m in UserRole}
        assert expected == actual


class TestSeverityLevel:
    def test_all_severities_exist(self):
        expected = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        actual = {m.value for m in SeverityLevel}
        assert expected == actual
