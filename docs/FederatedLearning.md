# Federated Learning Architecture Document

## Overview
This document details the design of the Federated Learning (FL) system using the **Flower (flwr)** framework to distributedly train the **FT-Transformer** model across multiple edge network nodes. The architecture prioritizes privacy, robustness against adversarial poisoning, and efficiency in handling tabular network flow data.

---

## 1. System Components

### 1.1 FL Server (Aggregator)
*   **Role:** Coordinates the federated rounds, aggregates model updates, manages client trust scores, and handles global model versioning.
*   **Implementation:** Python application running `flwr.server`.
*   **Storage:** Connects to PostgreSQL to log round metrics (accuracy, loss) and client trust states.

### 1.2 FL Client (Edge Node)
*   **Role:** Captures local tabular network flow data (e.g., via Ryu flow extractor), trains the FT-Transformer locally, and returns weight updates (gradients) to the server.
*   **Implementation:** Python application implementing `flwr.client.NumPyClient`. Wraps the PyTorch Tabular implementation of FT-Transformer.
*   **Inference:** In addition to training, the client actively runs inference on live traffic, sending DDoS alerts to the Mitigation Engine.

---

## 2. Communication & Synchronization

*   **Protocol:** Bidirectional **gRPC**.
*   **Security (mTLS):** Mutual TLS is enforced. The server authenticates the client's certificate, and the client authenticates the server's certificate.
*   **Synchronization:** 
    *   The server operates synchronously per round (`min_fit_clients` must be reached to start a round).
    *   Clients operate asynchronously locally but must return results within a configured timeout (`timeout` parameter in Flower strategy).
*   **Communication Compression:** To reduce the bandwidth overhead of sending FT-Transformer weights (which have large embedding tables), **Sparse Gradient Compression (Top-K Sparsification)** or **Quantization (INT8)** will be applied before transmitting parameters over the wire.

---

## 3. Data Distribution Strategies (IID vs. Non-IID)

Network traffic is inherently **Non-IID (Independent and Identically Distributed)**. Different edge nodes (e.g., an IoT gateway vs. a main web server switch) will see vastly different baseline traffic and attack distributions.

*   **Handling Non-IID Data:**
    *   **Algorithm choice:** Standard `FedAvg` suffers under high non-IID data. We will utilize an extended version of **FedProx** or a custom **Adaptive Trust Strategy**.
    *   FedProx adds a proximal term to the local client's loss function to restrict local updates from diverging too far from the global model, ensuring stable convergence despite highly skewed local datasets.

---

## 4. Robust Aggregation & Poisoning Defense

To defend against Byzantine clients (nodes compromised by an attacker attempting to poison the global model to ignore DDoS traffic).

### 4.1 Adaptive Trust Scoring
Instead of weighting client updates purely by the number of data samples they processed (standard FedAvg), the server maintains a dynamic **Trust Score ($T_i$)** for each client $i$.

1.  **Cosine Similarity:** In each round, the server calculates the cosine similarity between client $i$'s parameter update vector and the median update vector of all clients.
2.  **Trust Penalty:** If a client's update deviates significantly (low cosine similarity or large magnitude explosion), its $T_i$ is penalized.
3.  **Historical Trust:** $T_i$ is a moving average. Consistent good behavior slowly increases trust; erratic behavior rapidly drops it.
4.  **Weighting:** During aggregation, a client's contribution is scaled by $T_i \times \text{data\_samples}$.

### 4.2 Secure Aggregation (SecAgg)
*   **Objective:** Prevent the server (or an eavesdropper) from inspecting a specific client's individual raw gradients, preventing inference attacks.
*   **Mechanism:** Implemented using cryptographic Secure Multiparty Computation (SMPC). Clients mask their updates with paired cryptographic keys before sending them. The server can only decrypt the *sum* of the updates, never the individual vectors.

---

## 5. Differential Privacy (DP)

To ensure strict privacy compliance (GDPR) and prevent model inversion attacks.

*   **Local Differential Privacy (LDP):** 
    *   Implemented via **DP-SGD (Differentially Private Stochastic Gradient Descent)** on the client side using libraries like `Opacus`.
    *   **Mechanism:** 
        1.  **Gradient Clipping:** Limits the maximum $L_2$ norm of per-sample gradients to bound the influence of any single network flow.
        2.  **Noise Addition:** Injects zero-mean Gaussian noise ($\mathcal{N}(0, \sigma^2)$) to the gradients before sending them to the server.
*   **Trade-off:** Carefully tuning the clipping threshold ($C$) and noise multiplier ($\sigma$) is critical to ensure the FT-Transformer maintains high DDoS detection accuracy while satisfying ($\epsilon, \delta$)-DP guarantees.

---

## 6. Client Failure & Dropouts

Edge networks are volatile. The system is designed to be highly fault-tolerant.

*   **Quorum Requirements:** 
    *   `fraction_fit = 0.5`: Requests 50% of available clients to train.
    *   `min_fit_clients = 10`: The round will *not* start unless at least 10 clients are connected.
    *   `min_available_clients = 15`: Total pool must be at least 15.
*   **Handling Dropouts:** If a client disconnects during local training (e.g., node goes offline or timeout exceeded), the Flower server simply ignores that client for the current round. As long as `min_fit_clients` successfully return updates, the round successfully aggregates and increments.

---

## 7. Model Versioning & Lifecycle

1.  **Initialization:** A centralized server creates the initial untuned FT-Transformer architecture (Version `v0.0.1`).
2.  **Rounds:** The global model iterates through rounds (e.g., Round 1 to 100).
3.  **Checkpointing:** At the end of every successful round, the server saves the global PyTorch weights locally (e.g., `checkpoints/model_v1.0.45.pt`) and logs the round metadata to the PostgreSQL database.
4.  **Deployment:** The Mitigation Engine API polls the database for the latest `is_active = TRUE` model. Once a stable global model is achieved, administrators can tag a specific round's checkpoint as `production` via the Admin REST API, which triggers all edge nodes to pull and lock that specific version for active inference.
