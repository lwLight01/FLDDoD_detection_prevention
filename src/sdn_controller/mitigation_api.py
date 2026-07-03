"""
sdn_controller/mitigation_api.py
----------------------------------
Lightweight REST server embedded in Ryu to receive mitigation commands
from the Mitigation Engine and translate them into OpenFlow messages.

Accepts:
  POST /mitigation/block    — Hard DROP all packets from target_ip
  POST /mitigation/ratelimit — Install OFP Meter for rate limiting
  DELETE /mitigation/{rule_id} — Remove existing mitigation flow entry

Implementation deferred to Milestone 41.
Ref: docs/API.md § 2, docs/DevelopmentRoadmap.md — Milestone 41
"""
# TODO (Milestone 41): Implement Flask WSGI app inside Ryu wsgi framework
# TODO (Milestone 41): Implement block_ip, rate_limit, remove_rule handlers
