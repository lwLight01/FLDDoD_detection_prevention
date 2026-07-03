# REST API Specifications

## Overview
This document outlines the REST API exposed by the Mitigation Engine (FastAPI). It serves as the central control plane for the Dashboard, Edge Clients, and the SDN Controller.

---

## 1. Authentication & Users

### 1.1 Login (Get Access Token)
*   **URL:** `/api/v1/auth/login`
*   **Method:** `POST`
*   **Description:** Authenticates a user and returns a JWT access token.
*   **Request (application/x-www-form-urlencoded):**
    *   `username` (string, required)
    *   `password` (string, required)
*   **Response (200 OK):**
    ```json
    {
      "access_token": "eyJhbG...",
      "token_type": "bearer",
      "role": "ADMIN"
    }
    ```
*   **Status Codes:** `200 OK`, `401 Unauthorized`
*   **Validation:** Pydantic `OAuth2PasswordRequestForm`.
*   **Security:** None (Public).
*   **Rate Limiting:** 5 requests / minute per IP.

---

## 2. Mitigation & Firewall (SDN Integration)

### 2.1 Trigger Manual Mitigation
*   **URL:** `/api/v1/mitigation/trigger`
*   **Method:** `POST`
*   **Description:** Manually overrides autonomous logic to trigger a firewall rule.
*   **Request (application/json):**
    ```json
    {
      "target_ip": "10.0.0.5",
      "action_type": "BLOCK_IP",
      "duration_seconds": 3600,
      "reason": "Manual override by Admin"
    }
    ```
*   **Response (202 Accepted):**
    ```json
    {
      "status": "pending",
      "action_id": "uuid-1234",
      "message": "Mitigation command dispatched to Ryu controller."
    }
    ```
*   **Status Codes:** `202 Accepted`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`
*   **Validation:** `target_ip` must be valid IPv4/IPv6. `action_type` enum (`BLOCK_IP`, `RATE_LIMIT`, `ISOLATE`).
*   **Security:** Requires valid JWT. Role: `ADMIN` or `ANALYST`.
*   **Rate Limiting:** 20 requests / minute per user.

### 2.2 List Mitigation History
*   **URL:** `/api/v1/mitigation/history`
*   **Method:** `GET`
*   **Description:** Retrieves historical mitigation actions taken autonomously or manually.
*   **Request Params:** `limit` (int, default=50), `skip` (int, default=0), `status` (string, optional).
*   **Response (200 OK):**
    ```json
    [
      {
        "id": "uuid-1234",
        "target_ip": "10.0.0.5",
        "action_type": "BLOCK_IP",
        "executed_at": "2024-05-12T10:05:00Z",
        "status": "SUCCESS",
        "is_autonomous": true
      }
    ]
    ```
*   **Status Codes:** `200 OK`, `401 Unauthorized`
*   **Validation:** Query params validation (limit <= 1000).
*   **Security:** Requires valid JWT. Role: `ADMIN`, `ANALYST`, or `READONLY`.
*   **Rate Limiting:** 60 requests / minute per user.

---

## 3. Inference & Alerts (Edge Client -> Server)

### 3.1 Submit Threat Alert
*   **URL:** `/api/v1/inference/alert`
*   **Method:** `POST`
*   **Description:** Called by Edge Clients when the local FT-Transformer detects a DDoS flow.
*   **Request (application/json):**
    ```json
    {
      "client_id": "client-uuid",
      "flow_id": 987654321,
      "src_ip": "10.0.0.99",
      "prediction_probability": 0.98,
      "shap_values": {
        "tcp.flags.syn": 0.45,
        "flow.duration": 0.22
      },
      "timestamp": "2024-05-12T10:04:59Z"
    }
    ```
*   **Response (201 Created):**
    ```json
    {
      "status": "alert_logged",
      "alert_id": "alert-uuid",
      "mitigation_triggered": true
    }
    ```
*   **Status Codes:** `201 Created`, `400 Bad Request`, `401 Unauthorized`
*   **Validation:** `prediction_probability` between 0.0 and 1.0. `shap_values` must be a valid JSON map.
*   **Security:** mTLS (Mutual TLS) authenticated client certificate, OR edge-specific static API key.
*   **Rate Limiting:** 1000 requests / second per Edge Client.

---

## 4. Federated Communication State

*(Note: Actual model weights are transmitted via gRPC using Flower. These REST endpoints expose the state of the FL process to the dashboard).*

### 4.1 Get Global Model Status
*   **URL:** `/api/v1/federated/status`
*   **Method:** `GET`
*   **Description:** Returns the current state of the global FT-Transformer model.
*   **Response (200 OK):**
    ```json
    {
      "current_round": 45,
      "active_clients": 12,
      "global_accuracy": 0.992,
      "last_updated": "2024-05-12T09:00:00Z",
      "model_version": "v1.4.5"
    }
    ```
*   **Security:** Requires valid JWT. Role: `ADMIN`, `ANALYST`, `READONLY`.
*   **Rate Limiting:** 60 requests / minute per user.

### 4.2 Get Client Trust Scores
*   **URL:** `/api/v1/federated/trust-scores`
*   **Method:** `GET`
*   **Description:** Lists all FL clients and their current trust weights (used to defend against poisoning).
*   **Response (200 OK):**
    ```json
    [
      {"node_name": "edge-router-1", "trust_score": 0.99, "is_banned": false},
      {"node_name": "edge-router-2", "trust_score": 0.12, "is_banned": true}
    ]
    ```
*   **Security:** Requires valid JWT. Role: `ADMIN`, `ANALYST`.

---

## 5. Dashboard & Analytics

### 5.1 Get Traffic Statistics (Time-Series)
*   **URL:** `/api/v1/dashboard/traffic-stats`
*   **Method:** `GET`
*   **Description:** Aggregates flow statistics from TimescaleDB for visualization.
*   **Request Params:** `timeframe` (e.g., '1h', '24h', '7d').
*   **Response (200 OK):**
    ```json
    {
      "time_series": [
        {"timestamp": "2024-05-12T10:00:00Z", "total_flows": 1500, "attack_flows": 12},
        {"timestamp": "2024-05-12T10:05:00Z", "total_flows": 18000, "attack_flows": 16500}
      ]
    }
    ```
*   **Security:** Requires valid JWT.
*   **Rate Limiting:** 30 requests / minute.

### 5.2 Live Updates (WebSocket)
*   **URL:** `/ws/v1/dashboard/live`
*   **Method:** `WebSocket`
*   **Description:** Streams real-time attack alerts, new flow rules, and FL round completions to the frontend.
*   **Request:** JWT passed in initial handshake query param or headers.
*   **Security:** JWT verification on connection upgrade.

---

## 6. Logs & Monitoring

### 6.1 Get System Logs
*   **URL:** `/api/v1/logs/system`
*   **Method:** `GET`
*   **Description:** Fetches backend and SDN controller operational logs.
*   **Request Params:** `level` (INFO, WARN, ERROR), `limit` (int).
*   **Response (200 OK):**
    ```json
    [
      {"timestamp": "2024-05-12T10:05:01Z", "service": "ryu_controller", "level": "INFO", "message": "Installed OFPFlowMod for IP 10.0.0.5"}
    ]
    ```
*   **Security:** Requires valid JWT. Role: `ADMIN`.

### 6.2 Health Check
*   **URL:** `/api/v1/monitoring/health`
*   **Method:** `GET`
*   **Description:** Standard readiness/liveness probe for Docker/Kubernetes.
*   **Response (200 OK):**
    ```json
    {
      "status": "healthy",
      "database": "connected",
      "fl_server": "reachable",
      "ryu_controller": "reachable"
    }
    ```
*   **Security:** None (Public).
*   **Rate Limiting:** None.

---

## 7. Admin & Model Management

### 7.1 Force Global Model Deployment
*   **URL:** `/api/v1/admin/model/deploy`
*   **Method:** `POST`
*   **Description:** Forces the deployment of a specific FT-Transformer model version to all edge clients, overriding the standard FL schedule.
*   **Request (application/json):**
    ```json
    {
      "version_tag": "v1.4.5"
    }
    ```
*   **Status Codes:** `200 OK`, `403 Forbidden`, `404 Not Found`
*   **Security:** Requires valid JWT. Role: `ADMIN`.

### 7.2 Ban/Unban FL Client
*   **URL:** `/api/v1/admin/clients/{client_id}/ban`
*   **Method:** `PUT`
*   **Description:** Manually bans or unbans a client from participating in Federated Learning.
*   **Request (application/json):**
    ```json
    {
      "is_banned": true,
      "reason": "Suspicious gradient updates"
    }
    ```
*   **Security:** Requires valid JWT. Role: `ADMIN`.
