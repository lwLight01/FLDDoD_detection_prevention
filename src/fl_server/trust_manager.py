"""fl_server/trust_manager.py"""

from __future__ import annotations

from typing import Dict, List

import numpy as np


class TrustManager:
    """Scores FL clients based on gradient cosine similarity (Milestone 17).

    Each round, the median gradient vector is computed across all client
    updates.  Each client's cosine similarity to the median is measured and
    folded into a running EMA trust score.  A client whose score falls below
    ``auto_ban_threshold`` is permanently banned from aggregation.
    """

    def __init__(
        self,
        penalty_threshold: float = 0.7,
        auto_ban_threshold: float = 0.1,
        ema_alpha: float = 0.3,
    ) -> None:
        self._penalty_threshold = penalty_threshold
        self._auto_ban_threshold = auto_ban_threshold
        self._ema_alpha = ema_alpha

        self._scores: Dict[str, float] = {}
        self._banned: Dict[str, bool] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_score(self, client_id: str) -> float:
        """Return the current trust score for *client_id* (default 1.0)."""
        return self._scores.get(client_id, 1.0)

    def is_banned(self, client_id: str) -> bool:
        """Return True if the client has been auto-banned."""
        return self._banned.get(client_id, False)

    def get_weight(self, client_id: str, num_examples: int) -> float:
        """Return the effective aggregation weight for a client.

        Banned clients receive zero weight; otherwise the weight is the
        product of ``num_examples`` and the client's trust score.
        """
        if self.is_banned(client_id):
            return 0.0
        return float(num_examples) * self.get_score(client_id)

    def update_round(
        self, updates: Dict[str, List[np.ndarray]]
    ) -> Dict[str, float]:
        """Update trust scores based on one FL round of client gradients.

        Parameters
        ----------
        updates:
            Mapping of ``client_id → list[np.ndarray]`` (model parameters).

        Returns
        -------
        Dict mapping each client_id to its updated trust score.
        """
        if not updates:
            return {}

        # Flatten each client's parameter list into a single 1-D vector
        flat: Dict[str, np.ndarray] = {
            cid: np.concatenate([arr.ravel().astype(np.float64) for arr in arrays])
            for cid, arrays in updates.items()
        }

        # Compute element-wise median across all client vectors
        stacked = np.stack(list(flat.values()), axis=0)  # (n_clients, d)
        median_vec = np.median(stacked, axis=0)

        new_scores: Dict[str, float] = {}
        for cid, vec in flat.items():
            cos_sim = self._cosine_similarity(vec, median_vec)
            # Map cosine similarity [-1, 1] → trust penalty [0, 1]
            # sim=1 → factor=1.0; sim=-1 → factor=0.0
            trust_factor = (cos_sim + 1.0) / 2.0

            # Apply penalty when below threshold
            if cos_sim < self._penalty_threshold:
                trust_factor *= cos_sim if cos_sim > 0 else 0.0

            # EMA update
            prev = self._scores.get(cid, 1.0)
            updated = self._ema_alpha * trust_factor + (1.0 - self._ema_alpha) * prev
            updated = float(np.clip(updated, 0.0, 1.0))
            self._scores[cid] = updated
            new_scores[cid] = updated

            # Auto-ban check
            if updated < self._auto_ban_threshold:
                self._banned[cid] = True

        return new_scores

    def get_all_scores(self) -> Dict[str, float]:
        """Return a copy of the current scores dict."""
        return dict(self._scores)

    def get_banned_clients(self) -> List[str]:
        """Return a list of all currently banned client IDs."""
        return [cid for cid, banned in self._banned.items() if banned]

    def reset_client(self, client_id: str) -> None:
        """Restore a client's trust score to 1.0 and lift any ban."""
        self._scores[client_id] = 1.0
        self._banned[client_id] = False

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two 1-D numpy arrays."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0.0 or norm_b == 0.0:
            return 1.0  # Treat zero-vector as identical (neutral)
        return float(np.dot(a, b) / (norm_a * norm_b))
