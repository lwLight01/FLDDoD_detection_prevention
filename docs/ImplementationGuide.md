# Implementation Guide

This guide provides step-by-step instructions for deploying the Adaptive Privacy-Aware Federated Learning framework and the Autonomous Mitigation Engine.

## Prerequisites
- **OS:** Linux (Ubuntu 22.04 LTS recommended)
- **Docker:** v24.0+ and Docker Compose v2.0+
- **Python:** v3.10+
- **Mininet:** v2.3.0+

## 1. System Bring-up (Docker)

To launch the backend ecosystem (PostgreSQL Database, Ryu SDN Controller, and the FastAPI Mitigation API), use the provided Docker Compose file:

```bash
# Start all core services in detached mode
docker compose -f docker/docker-compose.mininet.yml up -d

# Verify services are running
docker compose -f docker/docker-compose.mininet.yml ps
```

## 2. Launching the Network Topology (Mininet)

The data plane is simulated using Mininet. This script creates the OpenVSwitch topology, connects it to the Ryu controller, and generates background traffic:

```bash
# Must be run as root
sudo python3 scripts/mininet_topo.py
```

## 3. Starting the Federated Learning System

The federated learning process involves one central aggregation server and multiple edge clients.

### 3.1 Start the Flower Server
In a new terminal window:
```bash
# Start the central aggregation server with Adaptive Trust Scoring
python3 -m src.fl_server.server --rounds 3 --min-clients 3
```

### 3.2 Start the Flower Clients
In separate terminal windows, start the simulated edge clients (assign unique client IDs):
```bash
python3 -m src.fl_client.client --client-id 1 --dataset data/client1.csv
python3 -m src.fl_client.client --client-id 2 --dataset data/client2.csv
python3 -m src.fl_client.client --client-id 3 --dataset data/client3.csv
```

## 4. End-to-End Mitigation Test

To trigger an autonomous mitigation event, run the attack generation script from an attacker node in Mininet:

```bash
# Inside the mininet CLI:
mininet> h2 ./scripts/attack_gen.sh 10.0.0.1 SYN_FLOOD
```

You can verify the autonomous mitigation by monitoring the Ryu controller logs or the FastAPI logs. A new OpenFlow rule will be pushed blocking or rate-limiting the attacker's IP dynamically.

## 5. Teardown

To shut down the entire ecosystem and clean up resources:

```bash
# Stop Docker services
docker compose -f docker/docker-compose.mininet.yml down -v

# Clean Mininet environment
sudo mn -c
```
