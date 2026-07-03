"""
mitigation_engine/services/rule_generator.py
----------------------------------------------
Policy Engine: Translates Risk Score + SHAP AttackContext → SDN/iptables rules.

Policy mapping (ref: docs/Mitigation.md § 3):
  Risk 50-70  → Stage 1: RATE_LIMIT  (e.g., SYN packets <= 10/sec on OVS meter)
  Risk 71-89  → Stage 2: ISOLATE     (e.g., reroute src_ip to DPI VLAN)
  Risk >= 90  → Stage 3: QUARANTINE  (e.g., hard DROP all packets from src_ip)

SHAP-driven precision:
  If top SHAP feature is "tcp_flags_syn" → apply TCP-SYN-specific rule.
  If top SHAP feature is "dst_port"      → block specific destination port.
  Fallback: broad IP-level rule.

Implementation deferred to Milestone 26.
Ref: docs/Mitigation.md § 3, docs/DevelopmentRoadmap.md — Milestone 26
"""

# TODO (Milestone 26): Implement RuleGenerator class
# TODO (Milestone 26): Implement generate_rule(risk_score, attack_context) -> MitigationRule
