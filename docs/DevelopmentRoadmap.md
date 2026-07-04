# Development Roadmap

## Phase 1: Research & Project Initialization (Milestones 1-5)

### Milestone 1: Finalize Architecture Documentation
*   **Objective:** Complete all high-level system design documents.
*   **Files:** `docs/Architecture.md`, `docs/ProjectStructure.md`
*   **Dependencies:** None
*   **Tests:** Peer review by academic supervisor.
*   **Deliverables:** Approved architecture diagrams.
*   **Estimated Time:** 1 week
*   **Acceptance Criteria:** All C4 diagrams and microservice definitions are finalized.
*   **Risk:** Low
*   **Priority:** High

### Milestone 2: Establish Git Repository & CI Pipeline
*   **Objective:** Set up version control, directory structure, and basic GitHub Actions.
*   **Files:** `.gitignore`, `.github/workflows/ci.yml`, folder structure setup.
*   **Dependencies:** M1
*   **Tests:** Trigger a test commit to verify CI linting passes.
*   **Deliverables:** Working repository with automated linting.
*   **Estimated Time:** 2 days
*   **Acceptance Criteria:** Empty project structure matches `ProjectStructure.md`.
*   **Risk:** Low
*   **Priority:** High

### Milestone 3: Provision Local Development Environment
*   **Objective:** Create scripts to initialize virtual environments and fetch datasets.
*   **Files:** `scripts/setup_env.sh`, `scripts/download_datasets.sh`, `requirements.txt`
*   **Dependencies:** M2
*   **Tests:** Run scripts on a clean machine; ensure no errors.
*   **Deliverables:** Automated environment setup scripts.
*   **Estimated Time:** 3 days
*   **Acceptance Criteria:** `pip install -r requirements.txt` succeeds; CIC-DDoS2019 dataset is downloaded.
*   **Risk:** Medium (OS-specific dependency issues)
*   **Priority:** High

### Milestone 4: Define Database Schema (Alembic Setup)
*   **Objective:** Implement SQLAlchemy models and initialize Alembic migrations.
*   **Files:** `src/mitigation_engine/db/models.py`, `alembic.ini`
*   **Dependencies:** M3
*   **Tests:** Unit tests verifying table creation in a local PostgreSQL instance.
*   **Deliverables:** Initial database migration script.
*   **Estimated Time:** 4 days
*   **Acceptance Criteria:** `alembic upgrade head` creates all tables defined in `Database.md` without error.
*   **Risk:** Medium (TimescaleDB extension configuration)
*   **Priority:** High

### Milestone 5: Configure Docker Compose for Core Services
*   **Objective:** Create the initial Docker Compose file for the DB and API scaffolding.
*   **Files:** `docker/docker-compose.yml`, `docker/mitigation_engine.Dockerfile`
*   **Dependencies:** M4
*   **Tests:** `docker-compose up -d` brings up Postgres and an empty FastAPI app.
*   **Deliverables:** Running local Docker cluster.
*   **Estimated Time:** 3 days
*   **Acceptance Criteria:** Containers stay running; API returns 200 OK on health check.
*   **Risk:** Low
*   **Priority:** High

---

## Phase 2: Data Engineering & Centralized Baseline (Milestones 6-12) ✅ COMPLETE

### Milestone 6: Raw Data Parsing (PCAP to CSV) ✅
*   **Objective:** Develop a script to extract tabular flow features from raw PCAPs using CICFlowMeter or Ryu offline.
*   **Files:** `notebooks/01_eda_and_cleaning.ipynb`
*   **Dependencies:** M3
*   **Tests:** Validate extracted CSV row count matches expected network flows.
*   **Deliverables:** Raw CSV dataset.
*   **Estimated Time:** 1 week
*   **Acceptance Criteria:** Dataset contains necessary features (Flow Duration, TCP flags, etc.) and a label column.
*   **Risk:** High (Data extraction tools can be buggy)
*   **Priority:** High

### Milestone 7: Exploratory Data Analysis (EDA) ✅
*   **Objective:** Analyze class imbalance, feature correlation, and distributions.
*   **Files:** `notebooks/01_eda_and_cleaning.ipynb`
*   **Dependencies:** M6
*   **Tests:** Visual inspection of correlation matrices.
*   **Deliverables:** Documented EDA findings.
*   **Estimated Time:** 3 days
*   **Acceptance Criteria:** Clear understanding of feature distributions to inform normalization.
*   **Risk:** Low
*   **Priority:** Medium

### Milestone 8: Data Normalization & Categorical Encoding ✅
*   **Objective:** Implement Quantile Transformers and Tokenizers for tabular data.
*   **Files:** `src/fl_client/dataset.py`
*   **Dependencies:** M7
*   **Tests:** Unit test verifying mean=0, std=1 for normalized continuous features.
*   **Deliverables:** PyTorch Datasets/DataLoaders.
*   **Estimated Time:** 4 days
*   **Acceptance Criteria:** Data pipeline successfully outputs tensors ready for model ingestion.
*   **Risk:** Medium (Handling unseen categorical tokens)
*   **Priority:** High

### Milestone 9: Data Splitting (Non-IID Simulation) ✅
*   **Objective:** Script to partition the master dataset into skewed subsets for FL clients.
*   **Files:** `scripts/create_fl_splits.py`
*   **Dependencies:** M8
*   **Tests:** Assert label distributions vary significantly across splits.
*   **Deliverables:** N distinct data partitions.
*   **Estimated Time:** 2 days
*   **Acceptance Criteria:** Partitions accurately reflect non-IID edge environments (e.g., one partition is mostly TCP, another mostly UDP).
*   **Risk:** Low
*   **Priority:** High

### Milestone 10: Implement Traditional Baseline Models ✅
*   **Objective:** Train Random Forest and XGBoost to establish performance benchmarks.
*   **Files:** `notebooks/02_centralized_baseline.ipynb`
*   **Dependencies:** M8
*   **Tests:** Cross-validation scoring.
*   **Deliverables:** Baseline accuracy/F1 metrics.
*   **Estimated Time:** 4 days
*   **Acceptance Criteria:** Achieved >95% F1 score with XGBoost on centralized data.
*   **Risk:** Low
*   **Priority:** High

### Milestone 11: Implement Centralized FT-Transformer ✅
*   **Objective:** Build and train the PyTorch Tabular FT-Transformer on the centralized dataset.
*   **Files:** `notebooks/03_ft_transformer_tuning.ipynb`, `src/fl_client/model.py`
*   **Dependencies:** M8
*   **Tests:** Validate forward pass tensor shapes.
*   **Deliverables:** Trained centralized FT-Transformer weights.
*   **Estimated Time:** 1 week
*   **Acceptance Criteria:** Centralized FT-Transformer outperforms or matches XGBoost baseline.
*   **Risk:** High (Transformer hyperparameter tuning on tabular data is difficult)
*   **Priority:** High

### Milestone 12: Integrate SHAP Explainability (Offline) ✅
*   **Objective:** Apply `shap.DeepExplainer` to the centralized FT-Transformer model.
*   **Files:** `notebooks/04_shap_analysis.ipynb`
*   **Dependencies:** M11
*   **Tests:** Verify SHAP value arrays match feature dimensions.
*   **Deliverables:** Visual SHAP summary plots.
*   **Estimated Time:** 3 days
*   **Acceptance Criteria:** SHAP accurately identifies synthetic attack signatures (e.g., highlights `TCP_SYN` for SYN floods).
*   **Risk:** Medium (DeepExplainer compatibility with custom PyTorch models)
*   **Priority:** High

---

## Phase 3: Federated Learning Implementation (Milestones 13-22)

### Milestone 13: Scaffold Flower Server
*   **Objective:** Implement the basic gRPC FL Server.
*   **Files:** `src/fl_server/main.py`
*   **Dependencies:** M11
*   **Tests:** Unit tests for server startup.
*   **Deliverables:** Runnable Flower Server.
*   **Estimated Time:** 2 days
*   **Acceptance Criteria:** Server starts and listens on default gRPC port.
*   **Risk:** Low
*   **Priority:** High

### Milestone 14: Scaffold Flower Client
*   **Objective:** Wrap the FT-Transformer in `flwr.client.NumPyClient`.
*   **Files:** `src/fl_client/client.py`
*   **Dependencies:** M11, M13
*   **Tests:** Connect client to server and trigger a dummy fit round.
*   **Deliverables:** Runnable Flower Client.
*   **Estimated Time:** 3 days
*   **Acceptance Criteria:** Client successfully connects, downloads weights, and uploads dummy gradients.
*   **Risk:** Low
*   **Priority:** High

### Milestone 15: Implement FedAvg Strategy
*   **Objective:** Complete an end-to-end standard FL round using FedAvg.
*   **Files:** `src/fl_server/strategy.py`
*   **Dependencies:** M14
*   **Tests:** Integration test running 3 local epochs across 2 clients.
*   **Deliverables:** Functional distributed training loop.
*   **Estimated Time:** 4 days
*   **Acceptance Criteria:** Global model loss decreases over 5 simulated rounds.
*   **Risk:** Medium (Serialization bottlenecks)
*   **Priority:** High

### Milestone 16: Implement FedProx for Non-IID
*   **Objective:** Add proximal term to client loss function to handle data skew.
*   **Files:** `src/fl_client/client.py`
*   **Dependencies:** M9, M15
*   **Tests:** Compare convergence rate of FedAvg vs FedProx on non-IID splits.
*   **Deliverables:** Updated client training logic.
*   **Estimated Time:** 1 week
*   **Acceptance Criteria:** FedProx demonstrates more stable convergence on the non-IID partitions than FedAvg.
*   **Risk:** High (Tuning the proximal coefficient $\mu$)
*   **Priority:** High

### Milestone 17: Develop Adaptive Trust Manager (Cosine Similarity)
*   **Objective:** Algorithm to penalize clients based on gradient deviation.
*   **Files:** `src/fl_server/trust_manager.py`
*   **Dependencies:** M15
*   **Tests:** Unit tests inputting outlier vectors and verifying trust score drop.
*   **Deliverables:** Trust scoring module.
*   **Estimated Time:** 1 week
*   **Acceptance Criteria:** Module correctly calculates median vector and assigns cosine penalties.
*   **Risk:** Medium (Mathematical edge cases)
*   **Priority:** High

### Milestone 18: Integrate Trust Strategy into Flower Server
*   **Objective:** Override standard aggregation to weight by Trust Score instead of just data volume.
*   **Files:** `src/fl_server/strategy.py`
*   **Dependencies:** M17
*   **Tests:** Simulated poisoning attack where the malicious client's weight is zeroed out by the strategy.
*   **Deliverables:** Custom FL Strategy class.
*   **Estimated Time:** 4 days
*   **Acceptance Criteria:** Global model accuracy is maintained even when 20% of clients are poisoned.
*   **Risk:** High
*   **Priority:** High

### Milestone 19: Local Differential Privacy (DP-SGD)
*   **Objective:** Integrate Opacus to clip gradients and add noise locally.
*   **Files:** `src/fl_client/client.py`, `src/fl_server/dp_manager.py`
*   **Dependencies:** M16
*   **Tests:** Assert gradients are bounded by clipping threshold $C$.
*   **Deliverables:** Differentially private client updates.
*   **Estimated Time:** 1 week
*   **Acceptance Criteria:** DP guarantees ($\epsilon < 5.0$) achieved with less than a 3% drop in F1 score.
*   **Risk:** High (Significant accuracy degradation if tuned poorly)
*   **Priority:** Medium

### Milestone 20: Server Checkpointing & DB Logging
*   **Objective:** Save global models and log round metrics to PostgreSQL.
*   **Files:** `src/fl_server/main.py`, Database schemas
*   **Dependencies:** M4, M18
*   **Tests:** Verify PostgreSQL `fl_rounds` table populates after a round.
*   **Deliverables:** Persistent FL state.
*   **Estimated Time:** 3 days
*   **Acceptance Criteria:** Models are saved to disk with corresponding DB records.
*   **Risk:** Low
*   **Priority:** High

### Milestone 21: Containerize FL Infrastructure
*   **Objective:** Add Server and Client to `docker-compose.yml`.
*   **Files:** `docker/fl_server.Dockerfile`, `docker/fl_client.Dockerfile`
*   **Dependencies:** M20
*   **Tests:** Spin up 1 server and 3 clients entirely via Docker Compose.
*   **Deliverables:** Dockerized FL cluster.
*   **Estimated Time:** 4 days
*   **Acceptance Criteria:** gRPC communication succeeds across Docker bridge network.
*   **Risk:** Medium (Docker networking issues)
*   **Priority:** High

### Milestone 22: Secure Aggregation (mTLS)
*   **Objective:** Generate certificates and enforce mTLS on the gRPC channels.
*   **Files:** `scripts/generate_certs.sh`
*   **Dependencies:** M21
*   **Tests:** Attempt connection without certs (should fail), attempt with certs (should succeed).
*   **Deliverables:** Secured gRPC communication.
*   **Estimated Time:** 3 days
*   **Acceptance Criteria:** FL communication is fully encrypted and authenticated.
*   **Risk:** Medium
*   **Priority:** High

---

## Phase 4: Autonomous Mitigation Engine (Milestones 23-31)

### Milestone 23: FastAPI Backend Scaffolding
*   **Objective:** Initialize endpoints and JWT authentication.
*   **Files:** `src/mitigation_engine/main.py`, `api/auth.py`
*   **Dependencies:** M5
*   **Tests:** Postman/curl login returns valid JWT.
*   **Deliverables:** Secure API gateway.
*   **Estimated Time:** 3 days
*   **Acceptance Criteria:** All endpoints require JWT unless specified otherwise.
*   **Risk:** Low
*   **Priority:** High

### Milestone 24: Alert Receiver Endpoint
*   **Objective:** API to ingest JSON alerts from edge clients.
*   **Files:** `src/mitigation_engine/api/alerts.py`
*   **Dependencies:** M23
*   **Tests:** POST mock alert JSON; verify it writes to DB.
*   **Deliverables:** Alert ingestion API.
*   **Estimated Time:** 2 days
*   **Acceptance Criteria:** Endpoint validates Pydantic schema and returns 201 Created.
*   **Risk:** Low
*   **Priority:** High

### Milestone 25: Implement Risk Scoring Engine
*   **Objective:** Code the mathematical risk formula combining probability, frequency, and decay.
*   **Files:** `src/mitigation_engine/services/analyzer.py`
*   **Dependencies:** M24
*   **Tests:** Unit tests asserting Risk Score increases sequentially with repeated alerts.
*   **Deliverables:** Dynamic risk module.
*   **Estimated Time:** 4 days
*   **Acceptance Criteria:** Formula outputs 0-100 score accurately reflecting threat level.
*   **Risk:** Medium (Formula tuning)
*   **Priority:** High

### Milestone 26: XAI Rule Generator (SHAP Translation)
*   **Objective:** Translate top SHAP features into specific mitigation strategies (e.g., TCP SYN limit).
*   **Files:** `src/mitigation_engine/services/rule_generator.py`
*   **Dependencies:** M25
*   **Tests:** Input mock SHAP values; assert correct policy type is selected.
*   **Deliverables:** Policy Engine.
*   **Estimated Time:** 1 week
*   **Acceptance Criteria:** System successfully maps SHAP strings to OpenFlow logic requirements.
*   **Risk:** High (Complex logic mapping)
*   **Priority:** High

### Milestone 27: SDN Client (Ryu REST Integration)
*   **Objective:** HTTP client to push JSON OpenFlow rules to the Ryu controller.
*   **Files:** `src/mitigation_engine/services/sdn_client.py`
*   **Dependencies:** M26
*   **Tests:** Mock Ryu server to test API payloads.
*   **Deliverables:** SDN communication layer.
*   **Estimated Time:** 3 days
*   **Acceptance Criteria:** Engine successfully dispatches correct JSON format to Ryu's REST interface.
*   **Risk:** Medium
*   **Priority:** High

### Milestone 28: TTL and Rollback Task Scheduler
*   **Objective:** Implement background tasks to expire mitigations.
*   **Files:** `src/mitigation_engine/services/scheduler.py`
*   **Dependencies:** M27
*   **Tests:** Set a 5-second TTL rule; assert deletion command is sent after 5 seconds.
*   **Deliverables:** Automated rule cleanup.
*   **Estimated Time:** 4 days
*   **Acceptance Criteria:** Mitigations automatically revert to Benign state when TTL expires.
*   **Risk:** Low
*   **Priority:** High

### Milestone 29: WebSockets for Live Alerts
*   **Objective:** Stream incoming alerts and mitigation actions to connected UI clients.
*   **Files:** `src/mitigation_engine/api/websocket.py`
*   **Dependencies:** M24
*   **Tests:** Connect dummy WebSocket client; trigger alert; verify message received.
*   **Deliverables:** Real-time data stream.
*   **Estimated Time:** 3 days
*   **Acceptance Criteria:** Latency between API receiving alert and WebSocket broadcast is < 50ms.
*   **Risk:** Low
*   **Priority:** Medium

### Milestone 30: Edge Client Inference Script
*   **Objective:** Write script for the Edge Node to actively ingest flows, run inference, generate SHAP, and call the Alert API.
*   **Files:** `src/fl_client/inference.py`, `src/fl_client/alert_sender.py`
*   **Dependencies:** M12, M24
*   **Tests:** Feed synthetic anomalous row; verify POST request reaches API.
*   **Deliverables:** Active inference agent.
*   **Estimated Time:** 1 week
*   **Acceptance Criteria:** Agent successfully triggers full pipeline (Detection -> XAI -> API Alert).
*   **Risk:** High (Inference latency must be very low)
*   **Priority:** High

### Milestone 31: Full Engine Integration Test
*   **Objective:** Verify entire flow from Alert POST to Ryu API command.
*   **Files:** `tests/integration/test_engine_to_ryu.py`
*   **Dependencies:** M28, M30
*   **Tests:** End-to-end integration test (mocking Ryu).
*   **Deliverables:** Validated Mitigation Engine.
*   **Estimated Time:** 2 days
*   **Acceptance Criteria:** 100% pass rate on integration suite.
*   **Risk:** Low
*   **Priority:** High

---

## Phase 5: Dashboard Frontend (Milestones 32-37)

### Milestone 32: React App Scaffolding & Routing
*   **Objective:** Initialize Vite/React app with TailwindCSS and React Router.
*   **Files:** `src/dashboard/App.tsx`, `package.json`
*   **Dependencies:** None
*   **Tests:** `npm run dev` loads empty framework.
*   **Deliverables:** Base frontend application.
*   **Estimated Time:** 2 days
*   **Acceptance Criteria:** Routes match the `Dashboard.md` specification.
*   **Risk:** Low
*   **Priority:** Medium

### Milestone 33: Authentication & State Management
*   **Objective:** Implement Login view, JWT storage, and Zustand store.
*   **Files:** `src/dashboard/hooks/useAuth.ts`
*   **Dependencies:** M23, M32
*   **Tests:** End-to-end login flow.
*   **Deliverables:** Secured frontend.
*   **Estimated Time:** 3 days
*   **Acceptance Criteria:** Unauthenticated users are redirected to login; JWT is passed in Axios headers.
*   **Risk:** Low
*   **Priority:** High

### Milestone 34: Home Dashboard & WebSocket Integration
*   **Objective:** Build high-level KPIs and connect the notification toast system.
*   **Files:** `src/dashboard/pages/Home.tsx`
*   **Dependencies:** M29, M33
*   **Tests:** Trigger mock WebSocket message; verify toast appears.
*   **Deliverables:** Live Home view.
*   **Estimated Time:** 4 days
*   **Acceptance Criteria:** Dashboard updates dynamically without page reloads.
*   **Risk:** Low
*   **Priority:** High

### Milestone 35: Attack Monitor & SHAP Visualization
*   **Objective:** Build the XAI interface using Recharts to display feature importances.
*   **Files:** `src/dashboard/pages/AttackMonitor.tsx`
*   **Dependencies:** M33
*   **Tests:** Verify SHAP bars render proportionally to values.
*   **Deliverables:** XAI View.
*   **Estimated Time:** 4 days
*   **Acceptance Criteria:** UI matches the wireframe in `Dashboard.md`.
*   **Risk:** Low
*   **Priority:** High

### Milestone 36: Federated Learning Status Views
*   **Objective:** Visualize training curves and client trust scores.
*   **Files:** `src/dashboard/pages/FLStatus.tsx`
*   **Dependencies:** M33
*   **Tests:** Load mock DB data into charts.
*   **Deliverables:** FL Monitoring views.
*   **Estimated Time:** 3 days
*   **Acceptance Criteria:** Training loss/accuracy charts are easily readable.
*   **Risk:** Low
*   **Priority:** Medium

### Milestone 37: Mitigation & Firewall Control Panel
*   **Objective:** View active rules and add Manual Override functionality.
*   **Files:** `src/dashboard/pages/Mitigation.tsx`
*   **Dependencies:** M21, M33
*   **Tests:** Submit manual rule; verify API 202 response.
*   **Deliverables:** Firewall control view.
*   **Estimated Time:** 4 days
*   **Acceptance Criteria:** Admins can successfully trigger manual rules via the UI.
*   **Risk:** Low
*   **Priority:** High

---

## Phase 6: Network Simulation (SDN) (Milestones 38-42)

### Milestone 38: Mininet Topology Definition
*   **Objective:** Python script to spin up simulated switches, normal hosts, and attacker hosts.
*   **Files:** `src/sdn_controller/mininet_topo.py`
*   **Dependencies:** Mininet installed on host/VM.
*   **Tests:** `pingall` succeeds between hosts.
*   **Deliverables:** Simulated network environment.
*   **Estimated Time:** 3 days
*   **Acceptance Criteria:** Multi-switch topology is created successfully.
*   **Risk:** Medium (Mininet quirks)
*   **Priority:** High

### Milestone 39: Ryu Controller Base App
*   **Objective:** Initialize OpenFlow 1.3 controller to handle basic L2 switching.
*   **Files:** `src/sdn_controller/ryu_app.py`
*   **Dependencies:** M38
*   **Tests:** Start Ryu; verify Mininet hosts can communicate through the controller.
*   **Deliverables:** Basic SDN controller.
*   **Estimated Time:** 4 days
*   **Acceptance Criteria:** Controller successfully installs basic forwarding rules.
*   **Risk:** Medium
*   **Priority:** High

### Milestone 40: Real-Time Flow Extraction
*   **Objective:** Modify Ryu app to calculate tabular features (duration, packet counts) and stream them to the Edge Client.
*   **Files:** `src/sdn_controller/flow_extractor.py`
*   **Dependencies:** M39
*   **Tests:** Run iperf; verify extracted CSV matches expected traffic.
*   **Deliverables:** Real-time data pipeline from Network to Model.
*   **Estimated Time:** 1.5 weeks
*   **Acceptance Criteria:** Extracted features precisely match the schema required by the FT-Transformer.
*   **Risk:** Very High (Time-synchronization and feature calculation accuracy)
*   **Priority:** Critical

### Milestone 41: Ryu Mitigation REST API
*   **Objective:** Small Flask/WSGI server inside Ryu to accept commands from the Mitigation Engine and translate them to OpenFlow.
*   **Files:** `src/sdn_controller/mitigation_api.py`
*   **Dependencies:** M27, M39
*   **Tests:** POST command from Mitigation Engine; verify Ryu installs the rule.
*   **Deliverables:** OpenFlow mitigation interface.
*   **Estimated Time:** 1 week
*   **Acceptance Criteria:** Controller successfully blocks/rate-limits IPs based on API calls.
*   **Risk:** High (OpenFlow specific rule syntax)
*   **Priority:** High

### Milestone 42: Traffic & Attack Generation Scripts
*   **Objective:** Bash scripts using `hping3` and `iperf` to simulate benign and malicious traffic.
*   **Files:** `scripts/traffic_gen.sh`, `scripts/attack_gen.sh`
*   **Dependencies:** M38
*   **Tests:** Run attack script; verify network congestion in Mininet.
*   **Deliverables:** Automated simulation triggers.
*   **Estimated Time:** 3 days
*   **Acceptance Criteria:** Scripts can simulate UDP Flood, SYN Flood, and slow HTTP attacks.
*   **Risk:** Low
*   **Priority:** Medium

---

## Phase 7: System Integration & Evaluation (Milestones 43-47)

### Milestone 43: End-to-End System Bring-up
*   **Objective:** Launch Mininet, Ryu, Flower Server, 3 Flower Clients, Mitigation API, and Dashboard simultaneously via Docker/Scripts.
*   **Files:** `docker/docker-compose.mininet.yml`
*   **Dependencies:** All previous.
*   **Tests:** Verify all services communicate.
*   **Deliverables:** Fully operational integrated system.
*   **Estimated Time:** 1 week
*   **Acceptance Criteria:** The entire ecosystem boots without crashing.
*   **Risk:** High (Integration hell)
*   **Priority:** Critical

### Milestone 44: End-to-End Mitigation Test
*   **Objective:** Run `attack_gen.sh`. Verify the flow goes through extraction, inference, SHAP, API alert, decision engine, Ryu API, and final OpenFlow block.
*   **Files:** `tests/system/test_end_to_end.py`
*   **Dependencies:** M43
*   **Tests:** Launch attack; measure Time-To-Mitigate (TTM).
*   **Deliverables:** Validated closed-loop defense.
*   **Estimated Time:** 1 week
*   **Acceptance Criteria:** Attack is successfully blocked autonomously within X seconds.
*   **Risk:** High
*   **Priority:** Critical

### Milestone 45: Poisoning Attack Simulation
*   **Objective:** Deploy a malicious Flower client that sends inverse gradients. Verify Adaptive Trust Manager isolates it.
*   **Files:** `tests/system/test_poisoning.py`
*   **Dependencies:** M18, M43
*   **Tests:** Monitor global accuracy during the attack.
*   **Deliverables:** Empirical proof of system robustness.
*   **Estimated Time:** 4 days
*   **Acceptance Criteria:** Global accuracy drops by < 5% during the attack, and the malicious client's trust score hits 0.
*   **Risk:** Medium
*   **Priority:** High

### Milestone 46: Performance Evaluation & Metrics Gathering
*   **Objective:** Collect latency, CPU overhead, FL communication bandwidth, and detection accuracy data.
*   **Files:** `docs/Experiments.md` (To be created)
*   **Dependencies:** M44, M45
*   **Tests:** Run extensive automated load tests.
*   **Deliverables:** Final quantitative results for the thesis/paper.
*   **Estimated Time:** 2 weeks
*   **Acceptance Criteria:** Statistically significant data collected across multiple runs.
*   **Risk:** Medium
*   **Priority:** High

### Milestone 47: Final Documentation & Open Source Release
*   **Objective:** Clean codebase, write `README.md` (Implementation Guide), and prep for GitHub release.
*   **Files:** `README.md`, `docs/ImplementationGuide.md`
*   **Dependencies:** M46
*   **Tests:** Fresh clone and setup by a 3rd party.
*   **Deliverables:** Public GitHub repository.
*   **Estimated Time:** 1 week
*   **Acceptance Criteria:** Documentation allows another researcher to replicate the exact setup.
*   **Risk:** Low
*   **Priority:** High
