"""fl_server/strategy.py"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple, Union

import os
import torch
import numpy as np
from flwr.common import (
    FitIns,
    FitRes,
    EvaluateRes,
    MetricsAggregationFn,
    NDArrays,
    Parameters,
    Scalar,
    ndarrays_to_parameters,
    parameters_to_ndarrays,
)
from flwr.server.client_manager import ClientManager
from flwr.server.client_proxy import ClientProxy
from flwr.server.strategy import FedAvg

from src.fl_server.trust_manager import TrustManager
from src.fl_server.db_logger import log_round_start, log_client_updates, log_round_completion
from src.fl_server.dp_manager import DPManager
from src.fl_server.config import settings


class AdaptiveTrustStrategy(FedAvg):
    """FedAvg extended with Adaptive Trust-weighted aggregation (M15/M17/M18).

    Overrides ``aggregate_fit`` to:
    1. Filter out permanently banned clients.
    2. Pass all client updates through the ``TrustManager`` to compute/update
       per-client trust scores.
    3. Aggregate parameters as a trust-and-data-volume weighted average
       instead of pure data-volume FedAvg.
    """

    def __init__(
        self,
        *,
        trust_manager: TrustManager,
        dp_manager: Optional[DPManager] = None,
        fraction_fit: float = 0.5,
        fraction_evaluate: float = 0.5,
        min_fit_clients: int = 2,
        min_evaluate_clients: int = 2,
        min_available_clients: int = 2,
        on_fit_config_fn: Optional[Callable[[int], Dict[str, Scalar]]] = None,
        on_evaluate_config_fn: Optional[Callable[[int], Dict[str, Scalar]]] = None,
        fit_metrics_aggregation_fn: Optional[MetricsAggregationFn] = None,
        evaluate_metrics_aggregation_fn: Optional[MetricsAggregationFn] = None,
        initial_parameters: Optional[Parameters] = None,
    ) -> None:
        
        # Merge DP config into fit config
        def custom_fit_config_fn(server_round: int) -> Dict[str, Scalar]:
            config = on_fit_config_fn(server_round) if on_fit_config_fn else {}
            if dp_manager:
                config.update(dp_manager.get_fit_config())
            return config

        super().__init__(
            fraction_fit=fraction_fit,
            fraction_evaluate=fraction_evaluate,
            min_fit_clients=min_fit_clients,
            min_evaluate_clients=min_evaluate_clients,
            min_available_clients=min_available_clients,
            on_fit_config_fn=custom_fit_config_fn,
            on_evaluate_config_fn=on_evaluate_config_fn,
            fit_metrics_aggregation_fn=fit_metrics_aggregation_fn,
            evaluate_metrics_aggregation_fn=evaluate_metrics_aggregation_fn,
            initial_parameters=initial_parameters,
        )
        self.trust_manager = trust_manager
        self.dp_manager = dp_manager
        
        # Checkpointing state
        self._round_db_ids: Dict[int, int] = {}

    # ------------------------------------------------------------------
    # Core override
    # ------------------------------------------------------------------

    def aggregate_fit(
        self,
        server_round: int,
        results: List[Tuple[ClientProxy, FitRes]],
        failures: List[Union[Tuple[ClientProxy, FitRes], BaseException]],
    ) -> Tuple[Optional[Parameters], Dict[str, Scalar]]:
        """Aggregate client updates using trust-weighted averaging."""
        if not results:
            return None, {}

        # 1. Filter out banned clients
        active_results = [
            (proxy, fit_res)
            for proxy, fit_res in results
            if not self.trust_manager.is_banned(proxy.cid)
        ]

        banned_count = len(results) - len(active_results)

        if not active_results:
            return None, {
                "round": server_round,
                "active_clients": 0,
                "banned_clients": banned_count,
            }

        # 2. Decode parameters for trust scoring
        client_updates: Dict[str, NDArrays] = {
            proxy.cid: parameters_to_ndarrays(fit_res.parameters)
            for proxy, fit_res in active_results
        }

        # 3. Update trust scores via TrustManager
        new_scores = self.trust_manager.update_round(client_updates)

        # 4. Compute trust-weighted aggregation
        aggregated_ndarrays = self._trust_weighted_aggregate(
            active_results, client_updates
        )
        
        # DB Logging: Start round and log client updates
        try:
            model_tag = f"v1.0.0-round-{server_round}"
            db_round_id = log_round_start(model_tag)
            self._round_db_ids[server_round] = db_round_id
            
            client_logs = []
            for proxy, fit_res in active_results:
                cid = proxy.cid
                banned = self.trust_manager.is_banned(cid)
                weight = self.trust_manager.get_weight(cid, fit_res.num_examples)
                
                # To calculate cosine similarity for the log, we can approximate 
                # or just pass a default since trust_manager does it internally.
                # For now, log the assigned trust score instead.
                client_logs.append({
                    "cid": cid,
                    "cosine_similarity": new_scores.get(cid, 1.0),
                    "assigned_trust_weight": weight,
                    "accepted": not banned
                })
                
            log_client_updates(db_round_id, client_logs)
        except Exception as e:
            print(f"[DB Logger] Failed to log round {server_round}: {e}")

        # 5. Re-filter: a client might have been banned THIS round
        if aggregated_ndarrays is None:
            return None, {
                "round": server_round,
                "active_clients": 0,
                "banned_clients": banned_count + len(active_results),
            }

        # Checkpointing: Save model to disk
        try:
            os.makedirs(settings.checkpoint_dir, exist_ok=True)
            ckpt_path = os.path.join(settings.checkpoint_dir, f"global_model_r{server_round}.pt")
            # In a real setup, we'd load these into a PyTorch model and use torch.save.
            # For simplicity, we save the NumPy arrays.
            torch.save(aggregated_ndarrays, ckpt_path)
        except Exception as e:
            print(f"[Checkpoint] Failed to save checkpoint: {e}")

        parameters_aggregated = ndarrays_to_parameters(aggregated_ndarrays)

        metrics: Dict[str, Scalar] = {
            "round": server_round,
            "active_clients": len(active_results),
            "banned_clients": banned_count + len(self.trust_manager.get_banned_clients()),
        }

        return parameters_aggregated, metrics

    def aggregate_evaluate(
        self,
        server_round: int,
        results: List[Tuple[ClientProxy, EvaluateRes]],
        failures: List[Union[Tuple[ClientProxy, EvaluateRes], BaseException]],
    ) -> Tuple[Optional[float], Dict[str, Scalar]]:
        """Aggregate evaluation metrics and log round completion."""
        loss_aggregated, metrics_aggregated = super().aggregate_evaluate(
            server_round, results, failures
        )
        
        # Log to DB
        db_round_id = self._round_db_ids.get(server_round)
        if db_round_id is not None:
            acc = metrics_aggregated.get("accuracy") if metrics_aggregated else None
            try:
                log_round_completion(
                    round_id=db_round_id,
                    global_loss=loss_aggregated,
                    global_accuracy=float(acc) if acc is not None else None
                )
            except Exception as e:
                print(f"[DB Logger] Failed to log round completion: {e}")
                
        return loss_aggregated, metrics_aggregated

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _trust_weighted_aggregate(
        self,
        results: List[Tuple[ClientProxy, FitRes]],
        client_updates: Dict[str, NDArrays],
    ) -> Optional[NDArrays]:
        """Weighted average of parameters: weight = trust_score × num_examples."""
        total_weight = 0.0
        weighted_params: Optional[List[np.ndarray]] = None

        for proxy, fit_res in results:
            cid = proxy.cid
            if self.trust_manager.is_banned(cid):
                continue

            weight = self.trust_manager.get_weight(cid, fit_res.num_examples)
            if weight <= 0.0:
                continue

            params = client_updates[cid]
            if weighted_params is None:
                weighted_params = [w * weight for w in params]
            else:
                for i, layer in enumerate(params):
                    weighted_params[i] = weighted_params[i] + layer * weight
            total_weight += weight

        if weighted_params is None or total_weight == 0.0:
            return None

        return [layer / total_weight for layer in weighted_params]
