"""
fl_client/client.py
-------------------
Flower NumPyClient implementation for the FT-Transformer edge node.

Implements:
  - fit(parameters, config): Receive global weights, run local training
    for `local_epochs` epochs, return updated weights + metrics.
  - evaluate(parameters, config): Load global weights, evaluate on
    local held-out validation set, return loss and accuracy.

Privacy:
  - DP-SGD (Opacus) wraps the optimizer during fit() (Milestone 19).
  - Gradients are clipped to MAX_GRAD_NORM before noise injection.

Non-IID Handling:
  - FedProx proximal term added to the training loss (Milestone 16):
      L_proximal = L_CE + (mu/2) * ||w - w_global||^2

Implementation deferred to Milestone 14 (base) and 16 (FedProx).

Ref: docs/FederatedLearning.md § 1.2, § 3
     docs/DevelopmentRoadmap.md — Milestones 14, 16, 19
"""

# TODO (Milestone 14): Implement DDosFlowerClient(flwr.client.NumPyClient)
# TODO (Milestone 16): Add proximal term to loss in fit()
# TODO (Milestone 19): Wrap optimizer with opacus.GradSampleModule
