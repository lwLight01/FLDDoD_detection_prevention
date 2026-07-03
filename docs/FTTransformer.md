# FT-Transformer Pipeline Architecture

## Overview
This document specifies the Machine Learning pipeline designed around the **FT-Transformer (Feature Tokenizer Transformer)**. FT-Transformer is uniquely suited for tabular data (network flows), as it transforms all features (both categorical and continuous) into embeddings, passing them through standard Transformer encoder blocks.

---

## 1. Data Preprocessing

### 1.1 Feature Engineering
The pipeline ingests raw network flow statistics (e.g., from OpenVSwitch/Ryu or CIC-DDoS2019 dataset).
*   **Selected Features (Examples):**
    *   *Categorical:* `Protocol` (TCP, UDP, ICMP), `TCP Flags` (SYN, ACK, FIN, RST, PSH, URG).
    *   *Continuous:* `Flow Duration`, `Total Fwd Packets`, `Total Bwd Packets`, `Fwd Packet Length Max/Min/Mean`, `Flow Bytes/s`, `Flow Packets/s`, `Init_Win_bytes_forward`, `Active Mean`, `Idle Mean`.
*   **Target:** `Label` (0 for Benign, 1 for DDoS). Multi-class (specific DDoS types) can be supported in future iterations.

### 1.2 Normalization (Continuous Features)
Transformers are highly sensitive to the scale of continuous inputs.
*   **Method:** **Quantile Transformer** or **Standard Scaler** (Z-score normalization).
*   *Justification:* Network flow distributions are heavily skewed (e.g., flow duration can be milliseconds or hours). Quantile transformation maps features to a normal distribution, preventing massive outliers from dominating the embedding layers.
*   *State Management:* The scaling parameters (mean, variance, or quantiles) calculated on the global/baseline dataset must be frozen and distributed to all Edge Clients to ensure consistent normalization during local Federated inference.

### 1.3 Categorical Encoding
*   **Method:** **Feature Tokenizer (Embedding Tables)**.
*   Unlike tree-based models which handle label-encoding, or standard MLPs which use One-Hot Encoding (OHE), the FT-Transformer assigns a unique trainable embedding vector to every unique category (e.g., Protocol=TCP gets a dense vector). Missing or unseen categories during inference are routed to a special `[UNK]` (unknown) embedding token.

---

## 2. Model Architecture & Hyperparameters

### 2.1 FT-Transformer Configuration
*   **Embedding Dimension ($d$):** `32` or `64`.
*   **Transformer Blocks (Depth):** `3` to `4` (kept shallow to minimize inference latency on edge nodes).
*   **Attention Heads:** `4` or `8`.
*   **Feed-Forward Dimension:** `4/3 * d` (e.g., `48` or `84`).
*   **Dropout:** `0.1` (Embedding dropout), `0.2` (Transformer block dropout).
*   **CLS Token:** A special `[CLS]` token is prepended to the feature tokens. The final state of this token is passed to the classification head.

### 2.2 Optimization & Loss
*   **Optimizer:** **AdamW** (Adam with Decoupled Weight Decay).
    *   *Weight Decay:* `1e-4` or `1e-5`.
*   **Loss Function:** **Binary Cross-Entropy with Logits (BCEWithLogitsLoss)**.
    *   *Justification:* More numerically stable than applying Sigmoid then standard BCELoss.
    *   *Class Imbalance Handling:* A `pos_weight` multiplier is applied to the BCE loss to penalize false negatives heavier than false positives, given that DDoS flows might be a minority class in normal operation windows.

### 2.3 Learning Rate & Scheduler
*   **Base Learning Rate:** `1e-3` or `5e-4`.
*   **Scheduler:** **Cosine Annealing with Warmup**.
    *   *Warmup Steps:* First 10% of local epochs slowly increase the LR to stabilize embedding initializations.
    *   *Decay:* Follows a cosine curve down to a minimum LR (e.g., `1e-6`).

---

## 3. Training & Evaluation Pipeline (Federated Context)

### 3.1 Local Training (Edge Client)
*   **Batch Size:** `256` or `512` (Tabular data allows for large batches, speeding up gradient computation).
*   **Local Epochs (per FL Round):** `1` to `3` (to prevent local overfitting and excessive proximal penalty in FedProx).
*   **Validation Split:** 20% of local data is held out to evaluate local loss before submitting gradients.

### 3.2 Evaluation Metrics
Computed both locally (on edge test sets) and globally (on a held-out server validation set, if available).
1.  **Macro F1-Score:** Primary metric, balancing Precision and Recall across Benign and Attack classes.
2.  **AUC-ROC:** Evaluates the model's ability to rank threats regardless of the chosen probability threshold.
3.  **False Positive Rate (FPR):** Critical metric. High FPR means dropping legitimate user traffic, which is unacceptable for a firewall system. Target FPR: $< 0.1\%$.

### 3.3 Checkpointing
*   **Local:** Clients do not persist model weights permanently; they hold them in memory, send updates, and await the aggregated global weights.
*   **Global (Server):** The Flower server serializes the aggregated `state_dict` using `torch.save` at the end of every round to `/checkpoints/round_{N}.pt`. The database logs the UUID and metadata of this file.

---

## 4. Real-time Inference & Mitigation Trigger

1.  **Data Ingestion:** The client receives a tabular row representing a closed network flow.
2.  **Preprocessing:** Applies the frozen global Normalization/Categorical Encoding.
3.  **Forward Pass:** Model outputs a raw logit.
4.  **Probability Calculation:** `Sigmoid(logit)`.
5.  **Thresholding:** If Probability $> 0.85$ (configurable threshold prioritizing high precision), a DDoS alert is triggered.

---

## 5. Explainability (SHAP Integration)

To move from "black-box" detection to "actionable intelligence", the pipeline incorporates **SHAP (SHapley Additive exPlanations)**.

### 5.1 SHAP Explainer
*   **Algorithm:** `shap.DeepExplainer` or `shap.GradientExplainer`.
*   **Background Dataset:** A small, representative subset of benign traffic (e.g., 1000 samples) is stored locally on the edge client to serve as the baseline for SHAP value calculation.

### 5.2 XAI Generation Flow
1.  **Trigger:** An anomalous flow crosses the $0.85$ probability threshold.
2.  **Calculation:** The client passes the specific flow tensor and the background dataset to the SHAP Explainer.
3.  **Output:** SHAP computes the marginal contribution of *every* feature (e.g., $SHAP_{TCP\_SYN} = +0.4$, $SHAP_{Flow\_Bytes} = -0.05$).
4.  **Actionable Insight:** The client sorts the SHAP values by magnitude. The top 3 features driving the malicious classification are extracted.
5.  **Transmission:** The Alert JSON sent to the Mitigation Engine includes these top SHAP values.

### 5.3 Utility in Mitigation
The Mitigation Engine reads the SHAP values. If SHAP indicates `TCP_SYN` is the highest contributing anomaly feature, the engine applies a specific *TCP SYN Rate Limit* rule rather than a blanket IP block, resulting in a highly precise, surgical mitigation strategy.
