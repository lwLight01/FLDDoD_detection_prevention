"""
sdn_controller/mininet_topo.py
--------------------------------
Mininet topology definition for the SDN simulation environment.

Topology (ref: docs/Architecture.md Deployment Diagram):
  - 2 OpenVSwitch instances (OVS1, OVS2)
  - 2 normal hosts (h1, h2) connected to OVS1
  - 1 attacker host (h3) connected to OVS2
  - 2 simulated Edge FL Client nodes embedded in hosts
  - Ryu controller connected to both OVS instances

Implementation deferred to Milestone 38.
Ref: docs/DevelopmentRoadmap.md — Milestone 38
"""

# TODO (Milestone 38): Implement DDoSTopology(Topo) class
# TODO (Milestone 38): Implement run_topology() with Ryu remote controller
