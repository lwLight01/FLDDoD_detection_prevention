"""
mitigation_engine/services/sdn_client.py
------------------------------------------
HTTP client that pushes OpenFlow rule commands to the Ryu controller REST API.

Ryu REST API endpoints used:
  POST /stats/flowentry/add     — Install a new flow entry
  DELETE /stats/flowentry/delete — Remove an existing flow entry
  POST /qos/rules/{dpid}        — Set QoS meter rules (rate limiting)

Implementation deferred to Milestone 27.
Ref: docs/Architecture.md § 10 (Communication Flow)
     docs/DevelopmentRoadmap.md — Milestone 27
"""

# TODO (Milestone 27): Implement SDNClient class using httpx.AsyncClient
# TODO (Milestone 27): Implement install_rule(rule) and remove_rule(rule_id)
