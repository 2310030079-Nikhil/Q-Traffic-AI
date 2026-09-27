"""
AQSA Stage 1 & 2: Traffic Intelligence, Feature Normalization,
and Adaptive Signal Priority Scoring.
"""

from typing import Dict, List, Any, Tuple
import numpy as np


class SignalPriorityScorer:
    """
    Computes dynamic priority scores for each intersection using traffic intelligence
    and dynamically adapted weight vectors.
    """

    def __init__(self, base_weights: Tuple[float, float, float, float, float] = (0.28, 0.24, 0.22, 0.14, 0.12)):
        # (w1: Congestion, w2: Queue, w3: WaitTime, w4: Density, w5: Uncertainty)
        self.base_weights = np.array(base_weights, dtype=float)
        self.current_weights = self.base_weights.copy()
        self.current_weights_dict = self.get_weights_dict()

    def get_weights_dict(self) -> Dict[str, float]:
        """
        Returns the current dynamically adapted weights as a named dictionary.
        """
        w = self.current_weights
        return {
            "w1_congestion": round(float(w[0]), 3),
            "w2_queue": round(float(w[1]), 3),
            "w3_wait_time": round(float(w[2]), 3),
            "w4_density": round(float(w[3]), 3),
            "w5_uncertainty": round(float(w[4]), 3),
        }

    def adapt_weights(
        self,
        traffic_states: Dict[str, Dict[str, Any]],
        uncertainties: Dict[str, Dict[str, Any]],
    ) -> Dict[str, float]:
        """
        Dynamically adjusts prioritization weights w1..w5 based on network-wide conditions:
        - If global uncertainty is elevated -> increase w5 (uncertainty penalty)
        - If queue variance across nodes is severe -> increase w2 (queue relief)
        - If global wait time is high -> increase w3 (delay alleviation)
        """
        w = self.base_weights.copy()

        # Extract network-wide aggregates
        queues = [s.get("queue_length", 0) for s in traffic_states.values()]
        waits = [s.get("avg_waiting_time", 0.0) for s in traffic_states.values()]
        uncs = [u.get("normalized_uncertainty", 0.1) for u in uncertainties.values()]

        # 1. Uncertainty adaptation
        mean_unc = float(np.mean(uncs)) if uncs else 0.1
        if mean_unc > 0.35:
            w[4] *= (1.0 + 1.2 * (mean_unc - 0.35))

        # 2. Queue variance adaptation
        q_std = float(np.std(queues)) if queues else 0.0
        if q_std > 8.0:
            w[1] *= (1.0 + 0.05 * min(15.0, q_std))

        # 3. Severe delay adaptation
        mean_wait = float(np.mean(waits)) if waits else 0.0
        if mean_wait > 30.0:
            w[2] *= (1.0 + 0.03 * min(20.0, mean_wait - 30.0))

        # Normalize weights to sum to 1.0
        w = w / np.sum(w)
        self.current_weights = w

        return {
            "w1_congestion": round(float(w[0]), 3),
            "w2_queue": round(float(w[1]), 3),
            "w3_wait_time": round(float(w[2]), 3),
            "w4_density": round(float(w[3]), 3),
            "w5_uncertainty": round(float(w[4]), 3),
        }

    def compute_priorities(
        self,
        traffic_states: Dict[str, Dict[str, Any]],
        uncertainties: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate normalized priority score for each intersection.
        Priority_i = w1*C_i + w2*Q_i + w3*W_i + w4*D_i + w5*U_i
        """
        self.adapt_weights(traffic_states, uncertainties)
        w = self.current_weights

        # Find network maxima for robust min-max normalization
        max_q = max(1.0, max([s.get("queue_length", 1) for s in traffic_states.values()]))
        max_w = max(1.0, max([s.get("avg_waiting_time", 1.0) for s in traffic_states.values()]))
        max_d = max(1.0, max([s.get("density", 1.0) for s in traffic_states.values()]))

        priorities: Dict[str, Dict[str, Any]] = {}

        for node_id, state in traffic_states.items():
            unc_info = uncertainties.get(node_id, {})
            u_norm = unc_info.get("normalized_uncertainty", 0.15)

            c_norm = float(np.clip(state.get("congestion_index", 0.0), 0.0, 1.0))
            q_norm = float(np.clip(state.get("queue_length", 0) / max_q, 0.0, 1.0))
            w_norm = float(np.clip(state.get("avg_waiting_time", 0.0) / max_w, 0.0, 1.0))
            d_norm = float(np.clip(state.get("density", 0.0) / max_d, 0.0, 1.0))

            priority = float(
                w[0] * c_norm +
                w[1] * q_norm +
                w[2] * w_norm +
                w[3] * d_norm +
                w[4] * u_norm
            )

            priorities[node_id] = {
                "intersection_id": node_id,
                "priority_score": round(priority, 3),
                "congestion_norm": round(c_norm, 3),
                "queue_norm": round(q_norm, 3),
                "wait_norm": round(w_norm, 3),
                "density_norm": round(d_norm, 3),
                "uncertainty_norm": round(u_norm, 3),
                "raw_queue": state.get("queue_length", 0),
                "raw_wait": state.get("avg_waiting_time", 0.0),
                "raw_uncertainty_margin": unc_info.get("confidence_margin", 0.0),
            }

        return priorities
