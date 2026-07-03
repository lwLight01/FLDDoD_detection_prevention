# Admin Dashboard Architecture

## Overview
The Dashboard is a Single Page Application (SPA) built with **React** and **TypeScript**, utilizing **TailwindCSS** for styling and **Recharts** for data visualization. It connects to the Mitigation Engine API via REST and WebSockets to provide real-time observability over the SDN, the federated training process, and automated mitigations.

---

## 1. Application Structure & Routing

*   `/` (Home): High-level system health and critical KPIs.
*   `/traffic`: Deep dive into live network flows and bandwidth usage.
*   `/attacks`: Active and historical DDoS alerts with SHAP explanations.
*   `/federated/clients`: Edge node management and trust score visualization.
*   `/federated/training`: Global model metrics (Accuracy, Loss) over FL rounds.
*   `/mitigation`: Active firewall rules and SDN OpenFlow modifications.
*   `/logs`: Searchable system and audit logs.
*   `/settings`: Global configuration, threshold tuning, and user management.

---

## 2. User Roles & RBAC

The UI strictly enforces Role-Based Access Control (RBAC) based on JWT claims.

*   **ADMIN:** Full read/write access. Can ban FL clients, manually trigger SDN rules, and promote global models to production.
*   **ANALYST:** Read-only access to all dashboards. Can view SHAP values and attack history, but cannot alter firewall rules or FL states.
*   **READONLY:** Restricted view. Only sees high-level KPIs (Home page) without exposing specific IP addresses or network topology.

---

## 3. Real-Time Alert System

*   **Mechanism:** Connected via WebSocket (`/ws/v1/dashboard/live`).
*   **UI Component:** A persistent "Notification Center" bell in the top-right navbar.
*   **Behavior:** When an edge client detects an attack > 0.85 probability, a toast notification immediately appears on screen (e.g., *"CRITICAL: UDP Flood detected from 10.0.0.5"*). The user can click the toast to jump directly to the `/attacks` view to see the SHAP justification.

---

## 4. Key Views & Wireframes

### 4.1 Home (Command Center)
**Purpose:** At-a-glance health of the entire defense ecosystem.
**Charts:** Sparklines for CPU/Memory, Donut chart for traffic composition.

```text
+-----------------------------------------------------------------------------+
| [Logo] AI DDoS Defense     [Home] [Attacks] [FL] [Mitigation]       [🔔(2)] |
+-----------------------------------------------------------------------------+
|  System Status: ONLINE  |  Active Mitigations: 12  |  FL Round: 45 (Stable) |
+-----------------------------------------------------------------------------+
|                                      |                                      |
|  [ Live Traffic (Last 1 Hour) ]      |  [ Recent Critical Alerts ]          |
|  |                                   |  🔴 10:04 - 10.0.0.5 - UDP Flood     |
|  |       /\        /\                |  🟠 09:55 - 192.168.1.1 - SYN Flood  |
|  |  /\  /  \    /\/  \               |  🟡 09:12 - 10.0.0.9 - Rate Limited  |
|  | /  \/    \  /      \              |                                      |
|  |/          \/                      |  [View All Attacks ->]               |
|  +-----------------------------      |                                      |
|                                      |                                      |
+-----------------------------------------------------------------------------+
|  [ Top Target Ports ]                |  [ Edge Node Trust Scores ]          |
|  (Donut Chart: 80, 443, 53)          |  Node A: 99% | Node B: 95% | ...     |
+-----------------------------------------------------------------------------+
```

### 4.2 Attack Monitor (XAI View)
**Purpose:** Detailed analysis of attacks using SHAP.
**Charts:** Horizontal Bar Chart for SHAP Feature Importances.

```text
+-----------------------------------------------------------------------------+
| Threat Details: Alert #98273                                                |
+-----------------------------------------------------------------------------+
| Attacker IP: 10.0.0.99               Target IP: 192.168.1.100               |
| Probability: 98.5%                   Classification: Malicious              |
+-----------------------------------------------------------------------------+
| [ SHAP Feature Contributions (Why was this flagged?) ]                      |
|                                                                             |
| tcp.flags.syn         [██████████████████████] +0.45                        |
| flow.bytes_s          [████████████] +0.25                                  |
| flow.duration         [████] +0.10                                          |
| fwd.packet.len.mean   [■■] -0.05                                            |
|                                                                             |
| Engine Insight: "High concentration of TCP SYN packets with zero payload."  |
+-----------------------------------------------------------------------------+
| Active Response: STAGE 1 (RATE_LIMITED) applied to SDN Switch #1.           |
| [ Escalate to BLOCK ]  [ Remove Rule ]                                      |
+-----------------------------------------------------------------------------+
```

### 4.3 Federated Learning - Training Status
**Purpose:** Monitor the convergence of the global model.
**Charts:** Multi-line graph tracking Loss and Accuracy.

```text
+-----------------------------------------------------------------------------+
| Global Model Training Metrics                                               |
+-----------------------------------------------------------------------------+
| Round: 45/100 | Active Clients: 12/15 | Current Acc: 99.2%                  |
+-----------------------------------------------------------------------------+
| [ Global Accuracy vs. Loss ]                                                |
|  1.0 |      /---------- (Accuracy)                                          |
|      |    /                                                                 |
|  0.5 |  /         \------ (Loss)                                            |
|      |/             \                                                       |
|  0.0 +---------------------------------                                     |
|      0       10      20      30      40 (Rounds)                            |
+-----------------------------------------------------------------------------+
| [ Force Deploy Model v1.4.5 to Production ]  (Admin Only)                   |
+-----------------------------------------------------------------------------+
```

### 4.4 Federated Learning - Client Trust
**Purpose:** Identify Byzantine or struggling edge nodes.

```text
+-----------------------------------------------------------------------------+
| Edge Client Management                                                      |
+-----------------------------------------------------------------------------+
| Node Name    | IP Address  | Data Size | Trust Score | Status   | Action    |
|--------------|-------------|-----------|-------------|----------|-----------|
| Router-Core  | 10.0.1.1    | 45,000    | 99.8%       | ACTIVE   | [Ban]     |
| IoT-Gateway  | 10.0.2.1    | 12,000    | 94.2%       | ACTIVE   | [Ban]     |
| Unknown-Node | 192.168.9.9 | 500       | 12.1%       | POISON?  | [BAN]     |
+-----------------------------------------------------------------------------+
```

### 4.5 Mitigation & Firewall
**Purpose:** View and manage the active state of the SDN controller and iptables.

```text
+-----------------------------------------------------------------------------+
| Active Mitigation Rules                                                     |
+-----------------------------------------------------------------------------+
| [ + Add Manual Rule ]                                                       |
|                                                                             |
| Target IP    | Action       | Origin     | Created At | TTL Expire | Action |
|--------------|--------------|------------|------------|------------|--------|
| 10.0.0.5     | BLOCK        | Autonomous | 10:04 AM   | 11:04 AM   | [Del]  |
| 10.0.1.9     | RATE_LIMIT   | Autonomous | 09:12 AM   | 09:42 AM   | [Del]  |
| 192.168.1.1  | ISOLATE      | Admin      | 08:00 AM   | Never      | [Del]  |
+-----------------------------------------------------------------------------+
```

---

## 5. Technology Choices
*   **React + TypeScript:** For type safety, predictability, and maintainability.
*   **TailwindCSS:** For rapid, responsive UI development without maintaining large CSS files.
*   **Recharts:** A composable charting library built on React components, perfect for time-series flow data and SHAP bar charts.
*   **Zustand:** For lightweight global state management (managing the WebSocket connection and user JWT state).
*   **Axios:** For standard REST API calls to the FastAPI backend.
