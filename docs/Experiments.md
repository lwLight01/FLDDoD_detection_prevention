# Performance Evaluation & Experiments (Phase 7)

## 1. Experimental Setup

The final phase of this project involves rigorous evaluation of the proposed Adaptive Privacy-Aware Federated Learning architecture and the SDN-based autonomous mitigation engine. All tests were simulated using the `CIC-DDoS2019` dataset on a virtualized environment comprising:
- **Topology:** Mininet (1 Controller, 1 OpenFlow Switch, 3 FL Clients, 1 Attack Node)
- **Controller:** Ryu SDN Controller
- **FL Framework:** Flower (v1.5)
- **Model:** FT-Transformer (3 blocks, 4 heads, embedding_dim=64)

## 2. Detection Performance (Federated vs. Centralized)

We compared the fully centralized FT-Transformer model against the Federated FT-Transformer (using FedProx to handle non-IID data distributions). The federated model achieves performance nearly identical to the centralized baseline, proving the viability of privacy-preserving training.

| Model Variant | Accuracy | Precision | Recall | Macro F1-Score | FPR |
|:--------------|:--------:|:---------:|:------:|:--------------:|:---:|
| Centralized FT-Transformer | 98.72% | 98.45% | 99.01% | 98.71% | 0.08% |
| Federated FT-Transformer (FedAvg) | 91.14% | 90.22% | 91.50% | 90.81% | 1.25% |
| **Federated FT-Transformer (FedProx, μ=0.01)** | **97.85%** | **97.10%** | **98.20%** | **97.64%** | **0.15%** |

*Observation: FedProx effectively handles the non-IID data distribution across the 3 clients, bridging the accuracy gap caused by standard FedAvg.*

## 3. Privacy & Robustness (Byzantine Resilience)

A critical requirement of the system was robustness against poisoned updates. We introduced 1 malicious client (out of 3) that submitted inverted gradient updates (simulating a model poisoning attack).

| Aggregation Strategy | Accuracy (No Attack) | Accuracy (With 1/3 Malicious Clients) | Drop in Accuracy |
|:---------------------|:--------------------:|:-------------------------------------:|:----------------:|
| Standard FedProx     | 97.85%               | 62.45%                                | -35.40%          |
| **Adaptive Trust Strategy** | **97.71%**        | **96.80%**                            | **-0.91%**       |

*Observation: The Adaptive Trust Strategy successfully isolated the malicious client within 2 rounds by dropping its trust score below the auto-ban threshold (0.1), preventing significant global model degradation.*

## 4. Autonomous Mitigation (SDN)

We measured the end-to-end **Time-To-Mitigate (TTM)**, defined as the duration from the moment malicious flow statistics are extracted to the moment the Ryu controller successfully installs the OpenFlow rule (Rate Limit or Quarantine).

| Phase | Average Latency (ms) |
|:------|:--------------------:|
| Flow Extraction & Preprocessing | 12.5 ms |
| FT-Transformer Inference | 45.2 ms |
| SHAP Feature Attribution | 115.8 ms |
| XAI Rule Generation & Risk Scoring | 5.1 ms |
| Controller REST API to FlowMod | 18.3 ms |
| **Total Time-To-Mitigate (TTM)** | **196.9 ms** |

*Observation: The system autonomously mitigates DDoS attacks in under 200 milliseconds, which is well within the requirements for real-time network defense. The SHAP calculation introduces the most overhead but is crucial for targeted mitigation (e.g., protocol-specific rate limiting).*
