# Deployment Architecture Document

## Overview
This document specifies the deployment lifecycle for the Autonomous DDoS Mitigation system. The architecture is designed to support a smooth transition from a localized research simulation (Docker Compose/Mininet) to a scalable, production-ready cloud or hybrid edge environment (Kubernetes).

---

## 1. Containerization (Docker)

The system is decomposed into highly specific, lightweight Docker images.
*   **Base Images:** `python:3.10-slim` for backend services, `node:18-alpine` for the dashboard frontend.
*   **Containers:**
    1.  `fl_server`: Flower gRPC aggregator.
    2.  `fl_client`: Edge node inference and local training.
    3.  `mitigation_engine`: FastAPI backend.
    4.  `dashboard`: React app served via Nginx.
    5.  `ryu_controller`: Ryu SDN controller (requires network capabilities).
    6.  `database`: TimescaleDB (PostgreSQL) image.

---

## 2. Local Research Deployment (Docker Compose)

For master's thesis evaluation and local development.

*   **Setup:** Managed via `docker-compose.yml`.
*   **Networking:** A dedicated bridge network (`ddos_net`) isolates the microservices.
*   **Mininet Integration:** The Ryu controller and `fl_client` containers are run with `--privileged` or specific `CAP_NET_ADMIN` capabilities to allow interaction with OpenVSwitch interfaces on the host machine.
*   **Volumes:** 
    *   `db_data:/var/lib/postgresql/data` (Database persistence)
    *   `./models:/app/models` (Bind mount for easy access to checkpointed weights)

---

## 3. Production Deployment (Kubernetes)

For real-world ISP or enterprise deployment, the system transitions to Kubernetes (K8s).

*   **Core Microservices:** Deployed as `Deployments` with multiple replicas (FastAPI Mitigation Engine, Dashboard).
*   **Stateful Services:** TimescaleDB is deployed as a `StatefulSet` with Persistent Volume Claims (PVCs) for reliable storage.
*   **Federated Learning Server:** Deployed as a `Deployment` exposed via a `ClusterIP` or `LoadBalancer` Service on the gRPC port.
*   **Edge Nodes (FL Clients):** Deployed as `DaemonSets` on specific edge-gateway nodes within the K8s cluster, or run as standalone Docker containers on remote branch office routers connecting back to the cloud K8s cluster.

---

## 4. Scaling Strategy

*   **Mitigation Engine (API):** Horizontally scalable via K8s Horizontal Pod Autoscaler (HPA) based on CPU utilization and incoming HTTP request rates.
*   **FL Clients:** Infinitely scalable horizontally. Adding more edge nodes distributes the inference load and enriches the federated training data.
*   **Database:** TimescaleDB chunks time-series data. If traffic exceeds single-node limits, it can be transitioned to a Multi-Node TimescaleDB cluster.

---

## 5. Monitoring & Logging

*   **Metrics (Prometheus & Grafana):**
    *   FastAPI endpoints expose `/metrics` (request latency, error rates).
    *   Flower Server exposes global accuracy and round duration.
    *   System metrics (CPU, RAM) collected via Node Exporter.
*   **Centralized Logging (ELK / Loki):**
    *   All Docker containers output logs to `stdout/stderr`.
    *   Logs are scraped by Fluentbit or Promtail and shipped to Elasticsearch or Grafana Loki.
    *   *Crucial for auditing:* Mitigation Actions (e.g., "Blocked IP X") are tagged as critical audit logs.

---

## 6. CI/CD Pipeline (GitHub Actions)

1.  **Pull Request (CI):**
    *   Linting (`flake8`, `black`).
    *   Unit Tests (`pytest`).
    *   Build Docker images (dry-run).
2.  **Merge to Main (CD):**
    *   Run Integration Tests.
    *   Build Docker images and tag with Git SHA.
    *   Push images to Docker Hub or AWS ECR.
    *   *(Optional)* Trigger K8s rollout restart or ArgoCD sync.

---

## 7. Secrets & Environment Variables

Strict separation of configuration from code.

### 7.1 Environment Variables (`.env`)
Passed directly into Docker Compose or managed via K8s ConfigMaps.
*   `DATABASE_URL=postgresql://user:pass@db:5432/ddos_db`
*   `RYU_REST_API_URL=http://ryu_controller:8080`
*   `FLOWER_SERVER_URL=fl_server:8080`
*   `JWT_SECRET_KEY` (MUST be injected securely)

### 7.2 Secrets Management
In production, `.env` files are insufficient.
*   **Implementation:** HashiCorp Vault or AWS Secrets Manager.
*   **Handled Secrets:** Database passwords, JWT signing keys, TLS/mTLS private certificates for gRPC secure aggregation, and Admin credentials.
