# Research Planning Document

## Project Title
Adaptive Privacy-Preserving Federated Learning using FT-Transformer for Intelligent DDoS Detection and Autonomous Multi-Stage Mitigation.

## 1. Problem Statement
The proliferation of Internet of Things (IoT) devices, cloud computing, and Software-Defined Networks (SDNs) has exponentially increased the attack surface for Distributed Denial of Service (DDoS) attacks. Modern DDoS attacks are highly distributed, sophisticated, and can adapt to evade traditional static rule-based defense mechanisms. While Machine Learning (ML) approaches offer dynamic detection capabilities, centralizing massive volumes of network traffic for training poses severe privacy risks, regulatory compliance challenges (e.g., GDPR), and single-point-of-failure vulnerabilities. Furthermore, existing decentralized approaches like Federated Learning (FL) often struggle with non-IID (Independent and Identically Distributed) network data, poisoning attacks from malicious clients, and fail to provide end-to-end autonomous mitigation in real-time. There is a critical need for a robust, privacy-preserving, and adaptive system capable of identifying complex DDoS patterns across distributed network nodes without compromising data privacy, while simultaneously initiating immediate, autonomous, and explainable mitigation strategies.

## 2. Motivation
DDoS attacks continue to be one of the most devastating cyber threats, capable of crippling critical infrastructure, financial services, and enterprise networks, leading to significant economic losses.
*   **Privacy Imperative:** Organizations are increasingly hesitant or legally restricted from sharing raw network traffic logs containing sensitive user data.
*   **Limitation of Traditional ML:** Centralized ML models introduce high latency in data transmission and violate privacy constraints.
*   **Need for Tabular Data Mastery:** Network traffic data is inherently tabular (flow statistics). Traditional Deep Learning models (like CNNs or standard LSTMs) often underperform compared to gradient boosting on tabular data. FT-Transformer (Feature Tokenizer Transformer) brings the power of Transformers specifically to tabular data, offering superior representation learning for complex network flows.
*   **Closing the Loop:** Detection without immediate, automated mitigation leaves networks vulnerable during the critical initial stages of an attack. A true defense system must seamlessly integrate intelligent detection with autonomous, multi-stage response mechanisms (e.g., via SDN controllers).

## 3. Research Objectives
1.  **Develop a Privacy-Preserving Detection Architecture:** Design and implement a Federated Learning framework that allows distributed network nodes to collaboratively train a DDoS detection model without sharing raw traffic data.
2.  **Optimize Tabular Deep Learning:** Adapt and optimize the FT-Transformer architecture specifically for network intrusion detection, focusing on high accuracy and low inference latency on tabular flow data.
3.  **Ensure Robustness against Adversaries:** Implement adaptive secure aggregation and differential privacy mechanisms to defend the federated learning process against poisoning attacks and inference attacks.
4.  **Implement Explainable AI (XAI):** Integrate SHAP (SHapley Additive exPlanations) to provide transparent, interpretable reasoning for model predictions, fostering trust and aiding network administrators in incident analysis.
5.  **Design Autonomous Mitigation:** Develop an autonomous multi-stage mitigation engine integrated with an SDN controller (e.g., Ryu) that dynamically applies defensive actions (rate limiting, flow rule blocking, traffic isolation) based on the detection model's outputs and explainability scores.

## 4. Research Questions
*   **RQ1:** How does the FT-Transformer perform compared to traditional state-of-the-art ML/DL models (e.g., Random Forest, XGBoost, MLP) in detecting zero-day and volumetric DDoS attacks using tabular network flow data?
*   **RQ2:** To what extent can an adaptive Federated Learning framework maintain high global model accuracy when confronted with highly non-IID network traffic distributions across diverse client nodes?
*   **RQ3:** How effectively can differential privacy and client trust scoring mechanisms mitigate the impact of malicious clients conducting model poisoning attacks within the federated setup?
*   **RQ4:** How can XAI (SHAP) be utilized not just for post-hoc analysis, but to dynamically inform and scale the severity of autonomous mitigation responses in an SDN environment?
*   **RQ5:** What is the end-to-end latency and resource overhead of the proposed integrated detection-to-mitigation pipeline in a simulated SDN architecture under heavy attack load?

## 5. Research Gap
While substantial research exists in ML-based DDoS detection and Federated Learning, several critical gaps remain:
*   **Underutilization of Transformers for Tabular Network Data:** Most deep learning IDS/DDoS solutions force-fit spatial (CNN) or sequential (RNN) models onto tabular flow data. FT-Transformer is specifically designed for tabular data but is largely unexplored in federated network security.
*   **Lack of Robustness in FL:** Many FL intrusion detection systems assume benign clients. They lack robust defense mechanisms (like adaptive aggregation based on trust scores) against targeted poisoning attacks or fail to guarantee formal differential privacy.
*   **Disconnect between Detection and Mitigation:** The vast majority of academic research stops at detection (classification). There is a significant gap in creating closed-loop systems that directly translate AI decisions into actionable, automated SDN mitigation strategies.
*   **Black-box Decision Making:** ML models are often deployed as black boxes. In cybersecurity, actionable intelligence requires explainability. The integration of XAI directly into the automated mitigation logic is highly novel.

## 6. Existing Solutions
1.  **Centralized ML/DL IDS:** Solutions utilizing Random Forest, SVM, CNNs, or LSTMs trained on centralized datasets (e.g., CIC-DDoS2019, UNSW-NB15).
2.  **Standard Federated Learning for IDS:** Basic FedAvg implementations for intrusion detection across multiple domains.
3.  **SDN-based Heuristic Mitigation:** Rule-based or threshold-based DDoS mitigation strategies implemented via SDN controllers (e.g., entropy-based detection).
4.  **Blockchain-assisted FL:** Using blockchain for secure model aggregation, though often suffering from high latency and scalability issues.

## 7. Why Existing Papers are Insufficient
*   **Centralized approaches** fail privacy requirements and cannot scale across distinct organizational boundaries without exposing sensitive data.
*   **Standard FL (FedAvg)** degrades significantly under non-IID conditions common in distinct network topologies and is highly vulnerable to Byzantine failures (poisoned updates).
*   **Heuristic SDN defenses** struggle to detect low-rate or highly distributed, sophisticated application-layer DDoS attacks.
*   Existing literature mostly treats **XAI as an afterthought** (for dashboard visualization) rather than an active component driving mitigation severity.

## 8. Proposed Contribution
This research proposes a holistic, end-to-end framework with the following contributions:
1.  **Novel Application of FT-Transformer:** First comprehensive application of FT-Transformer for DDoS detection within a Federated Learning context.
2.  **Adaptive Robust Aggregation:** A novel client aggregation algorithm that assigns dynamic trust scores based on model update deviations and historical reliability, effectively neutralizing poisoning attacks.
3.  **Privacy-Utility Trade-off Optimization:** Integration of local differential privacy mechanisms tailored for FT-Transformer gradients.
4.  **XAI-Driven Autonomous Mitigation Engine:** A uniquely designed engine that translates FT-Transformer probabilities and SHAP feature importance into multi-stage SDN flow rules (e.g., isolating specific ports or protocols identified as malicious by SHAP).

## 9. Novelty
The primary novelty lies in the **convergence** of these advanced paradigms: employing **FT-Transformer** (optimal for tabular flow data) within a **robust, privacy-preserving FL framework**, and actively using **XAI (SHAP) to parameterize real-time SDN mitigation rules**. This creates a truly autonomous, intelligent, and explainable defense-in-depth system that addresses both detection accuracy and actionable response simultaneously.

## 10. Expected Outcomes
*   A fully functional, containerized prototype of the distributed architecture.
*   Empirical evidence demonstrating the superiority of FT-Transformer on tabular network datasets compared to traditional baselines.
*   Demonstrable resilience against data poisoning and non-IID data distributions in the federated network.
*   Quantifiable metrics showing reduced mitigation latency and improved network availability during simulated DDoS attacks in Mininet/Ryu.
*   A high-impact IEEE journal/conference publication.

## 11. Research Methodology
1.  **Phase 1: Literature Review & Architecture Design:** Comprehensive review of FT-Transformer, robust FL, and SDN mitigation. Finalize system architecture and APIs.
2.  **Phase 2: Data Preprocessing & Centralized Baseline:** Select datasets, perform feature engineering, and train a centralized FT-Transformer model to establish upper-bound performance metrics.
3.  **Phase 3: Federated Learning Implementation:** Develop the Flower-based FL framework. Implement standard FedAvg, followed by the proposed adaptive trust-based aggregation.
4.  **Phase 4: Privacy & Security Hardening:** Integrate Differential Privacy and simulate poisoning attacks to evaluate the robustness of the adaptive aggregation.
5.  **Phase 5: XAI & Mitigation Engine:** Integrate SHAP. Develop the FastAPI backend and the autonomous mitigation logic that communicates with the Ryu SDN controller.
6.  **Phase 6: SDN Simulation & Integration:** Set up the Mininet topology. Connect the Ryu controller to the mitigation engine. Conduct end-to-end testing with simulated attack traffic.
7.  **Phase 7: Evaluation & Analysis:** Rigorous statistical evaluation of detection metrics, system latency, and mitigation effectiveness.
8.  **Phase 8: Documentation & Writing:** Finalize all architectural documents, draft the master's thesis, and prepare the IEEE manuscript.

## 12. Technology Stack
*   **Machine Learning:** PyTorch, PyTorch Tabular (for FT-Transformer), Scikit-Learn.
*   **Federated Learning:** Flower (flwr).
*   **Explainable AI:** SHAP.
*   **Backend & APIs:** FastAPI, Uvicorn, Python 3.10+.
*   **Database:** PostgreSQL (for logs, metrics, and client trust states), SQLAlchemy.
*   **SDN & Network Simulation:** Mininet, Ryu Controller, OpenVSwitch.
*   **Frontend/Dashboard:** React, TypeScript, TailwindCSS, Recharts.
*   **Deployment & Containerization:** Docker, Docker Compose.

## 13. Dataset Selection
To ensure robust evaluation across different attack vectors, the following datasets will be utilized:
1.  **CIC-DDoS2019:** A comprehensive and widely accepted dataset containing diverse, modern DDoS attack types (Reflection, Exploitation, Application layer).
2.  **UNSW-NB15:** Used to test the model's generalizability against a broader spectrum of network intrusions beyond just DDoS.
3.  **Edge-IIoTset:** (Optional but recommended) To specifically evaluate performance in IoT-heavy network environments.

## 14. Evaluation Metrics
*   **Detection Metrics:** Accuracy, Precision, Recall, F1-Score, Area Under the ROC Curve (AUC-ROC), False Positive Rate (FPR), False Negative Rate (FNR).
*   **Federated Metrics:** Convergence rate (communication rounds needed), Global model accuracy under non-IID settings, Robustness against poisoning (accuracy drop percentage).
*   **System/Mitigation Metrics:** End-to-end latency (from packet arrival to rule installation), Controller CPU/Memory overhead, Network throughput during mitigation, Time to mitigate (TTM).

## 15. Baseline Models
The proposed FT-Transformer FL system will be benchmarked against:
*   **Centralized Baselines:** Random Forest, XGBoost, Multi-Layer Perceptron (MLP), Standard CNN/LSTM on the same datasets.
*   **Federated Baselines:** Standard FedAvg (without trust scoring), FedProx (for non-IID handling comparison).

## 16. Risk Analysis
*   **Risk:** High computational overhead of FT-Transformer on edge clients.
    *   **Mitigation:** Model pruning/quantization techniques, or delegating computation to edge servers rather than endpoint devices.
*   **Risk:** SDN Controller bottleneck during massive volumetric attacks.
    *   **Mitigation:** Implement proactive flow rules, rate-limiting at the switch level, and ensure the mitigation engine batches rule updates.
*   **Risk:** Flower framework connectivity issues in simulated environments.
    *   **Mitigation:** Extensive containerized testing and utilizing stable gRPC communication protocols.

## 17. Future Extensions
*   **Integration with P4/Programmable Switches:** Moving mitigation logic directly into the data plane for line-rate dropping of malicious packets.
*   **Cross-Silo Federated Learning:** Expanding the architecture to allow collaboration between different Internet Service Providers (ISPs) rather than just intra-organizational nodes.
*   **Dynamic Feature Selection:** Implementing reinforcement learning to dynamically select which flow features are most relevant based on the current attack landscape, reducing processing overhead.
