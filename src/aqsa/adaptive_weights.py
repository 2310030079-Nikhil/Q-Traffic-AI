"""
Dynamic traffic objective weight calculation for QUBO formulation.
Calculates linear delay-reduction rewards and quadratic arterial green-wave coordination terms.
"""

from typing import Dict, List, Any, Tuple
import numpy as np


class AdaptiveWeightGenerator:
    """
    Generates dynamic objective coefficients reflecting real-time queue lengths,
    predicted volumes, waiting times, and corridor coordination.
    """

    def __init__(
        self,
        weight_delay: float = 0.40,
        weight_queue: float = 0.35,
        weight_switch: float = 0.15,
        weight_coord: float = 0.10,
    ):
        self.w_delay = weight_delay
        self.w_queue = weight_queue
        self.w_switch = weight_switch
        self.w_coord = weight_coord

    def compute_linear_terms(
        self,
        variable_meta: Dict[str, Dict[str, Any]],
        traffic_states: Dict[str, Dict[str, Any]],
        predictions: Dict[str, Dict[str, Any]],
        priorities: Dict[str, Dict[str, Any]],
    ) -> np.ndarray:
        """
        Compute linear coefficient vector for binary variables.
        Negative coefficients represent benefits (minimizing x^T Q x).
        """
        n = len(variable_meta)
        linear_terms = np.zeros(n, dtype=float)

        for idx, (var_name, meta) in enumerate(variable_meta.items()):
            node_id = meta["intersection_id"]
            phase = meta["phase"]  # 'NS' or 'EW'

            state = traffic_states.get(node_id, {})
            pred = predictions.get(node_id, {})
            p_score = priorities.get(node_id, {}).get("priority_score", 0.5)

            # Split queue and wait time between approaches (NS vs EW)
            raw_queue = state.get("queue_length", 10)
            raw_wait = state.get("avg_waiting_time", 15.0)
            pred_vol = pred.get("target_volume", {}).get("prediction", 40.0)

            # Estimate directional pressure
            if phase == "NS":
                # In typical grid, consider current phase state
                is_currently_active = "NS" in state.get("current_phase", "NS_GREEN")
                # Bias coefficient towards clearing larger NS queues
                direction_pressure = (raw_queue * 0.55 + raw_wait * 0.35 + pred_vol * 0.25)
            else:
                is_currently_active = "EW" in state.get("current_phase", "NS_GREEN")
                direction_pressure = (raw_queue * 0.45 + raw_wait * 0.35 + pred_vol * 0.25)

            # Switching penalty: if switching away from currently active phase, add small lost clearance penalty
            switch_penalty = 0.0 if is_currently_active else (2.5 * self.w_switch)

            # Objective: minimize delay -> negative linear reward for granting green
            # Priority scales the magnitude of the reward
            reward = -1.0 * (direction_pressure * 0.2) * (1.0 + 0.8 * p_score)
            linear_terms[idx] = reward + switch_penalty

        return linear_terms

    def compute_quadratic_coordination_terms(
        self,
        variable_meta: Dict[str, Dict[str, Any]],
        priorities: Dict[str, Dict[str, Any]],
        adjacent_pairs: List[Tuple[str, str]] = None,
    ) -> Dict[Tuple[int, int], float]:
        """
        Computes corridor green-wave coordination bonus between adjacent intersections.
        Simultaneous green along the same arterial reduces corridor trip time.
        """
        var_names = list(variable_meta.keys())
        var_to_idx = {name: idx for idx, name in enumerate(var_names)}
        quad_terms: Dict[Tuple[int, int], float] = {}

        if not adjacent_pairs:
            # Default adjacent neighbors for 4-node grid: (A,B), (A,C), (B,D), (C,D)
            adjacent_pairs = [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")]

        for u, v in adjacent_pairs:
            # NS synchronization between vertically or horizontally connected nodes
            ns_u, ns_v = f"{u}_phase_NS", f"{v}_phase_NS"
            ew_u, ew_v = f"{u}_phase_EW", f"{v}_phase_EW"

            if ns_u in var_to_idx and ns_v in var_to_idx:
                i, j = min(var_to_idx[ns_u], var_to_idx[ns_v]), max(var_to_idx[ns_u], var_to_idx[ns_v])
                p_u = priorities.get(u, {}).get("priority_score", 0.5)
                p_v = priorities.get(v, {}).get("priority_score", 0.5)
                # Coordination bonus (negative in minimization)
                bonus = -1.8 * self.w_coord * (p_u + p_v)
                quad_terms[(i, j)] = quad_terms.get((i, j), 0.0) + bonus

            if ew_u in var_to_idx and ew_v in var_to_idx:
                i, j = min(var_to_idx[ew_u], var_to_idx[ew_v]), max(var_to_idx[ew_u], var_to_idx[ew_v])
                p_u = priorities.get(u, {}).get("priority_score", 0.5)
                p_v = priorities.get(v, {}).get("priority_score", 0.5)
                bonus = -1.8 * self.w_coord * (p_u + p_v)
                quad_terms[(i, j)] = quad_terms.get((i, j), 0.0) + bonus

        return quad_terms
