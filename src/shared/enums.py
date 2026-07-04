"""shared/enums.py"""

from enum import Enum


class AttackType(str, Enum):
    """Classification labels for DDoS attack categories."""

    BENIGN = "BENIGN"
    UDP_FLOOD = "UDP_FLOOD"
    SYN_FLOOD = "SYN_FLOOD"
    HTTP_FLOOD = "HTTP_FLOOD"
    DNS_AMPLIFICATION = "DNS_AMPLIFICATION"
    UNKNOWN = "UNKNOWN"


class MitigationLevel(str, Enum):
    """Multi-stage mitigation escalation levels."""

    NONE = "NONE"  # Risk < 50  — no action
    RATE_LIMIT = "RATE_LIMIT"  # Risk 50-70 — Stage 1
    ISOLATE = "ISOLATE"  # Risk 71-89 — Stage 2
    QUARANTINE = "QUARANTINE"  # Risk >= 90 — Stage 3


class MitigationStatus(str, Enum):
    """Lifecycle status of a mitigation action record."""

    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REVOKED = "REVOKED"


class UserRole(str, Enum):
    """RBAC roles for the admin dashboard."""

    ADMIN = "ADMIN"
    ANALYST = "ANALYST"
    READONLY = "READONLY"


class SeverityLevel(str, Enum):
    """Severity tiers for alert classification."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
