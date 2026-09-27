"""
Dynamic QUBO Generator assembling linear, quadratic, and adaptive constraint penalty terms.
"""

from typing import Dict, List, Any, Tuple
import numpy as np
from src.aqsa.adaptive_weights import AdaptiveWeightGenerator
from src.aqsa.penalty import AdaptivePenaltyManager


class DynamicQUBOBuilder:
    """
    Constructs an adaptive QUBO matrix Q such that min x^T Q x optimizes traffic
    delay, queue dissipation, signal switching, and enforces safety constraints.
    """

    def __init__(
        self,
        base_penalty: float = 8.0,
        penalty_scale: float = 1.5,
    ):
        self.weight_gen = AdaptiveWeightGenerator()
        self.penalty_mgr = AdaptivePenaltyManager(base_penalty=base_penalty, scaling_factor=penalty_scale)

    def build_qubo(
        self,
        selection_result: Dict[str, Any],
        traffic_states: Dict[str, Dict[str, Any]],
        predictions: Dict[str, Dict[str, Any]],
        priorities: Dict[str, Dict[str, Any]],
        adjacent_pairs: List[Tuple[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Assemble upper-triangular QUBO matrix and associated metadata.
        """
        var_names = selection_result["quantum_variables"]
        var_meta = selection_result["variable_meta"]
        n = len(var_names)

        if n == 0:
            return {"matrix": np.zeros((0, 0)), "qubo_dict": {}, "variables": [], "dimension": 0}

        Q = np.zeros((n, n), dtype=float)

        # 1. Linear traffic rewards & switching costs
        linear_traffic = self.weight_gen.compute_linear_terms(
            variable_meta=var_meta,
            traffic_states=traffic_states,
            predictions=predictions,
            priorities=priorities,
        )

        # 2. Quadratic coordination terms (green waves along arterials)
        quad_coord = self.weight_gen.compute_quadratic_coordination_terms(
            variable_meta=var_meta,
            priorities=priorities,
            adjacent_pairs=adjacent_pairs,
        )

        # 3. Adaptive constraint penalties
        penalties = self.penalty_mgr.get_penalties_for_variables(
            variable_meta=var_meta,
            priorities=priorities,
        )

        # Populate diagonal with linear terms + linear penalty components
        for i in range(n):
            Q[i, i] = linear_traffic[i] + penalties["linear_penalties"].get(i, 0.0)

        # Populate off-diagonal terms with coordination + quadratic constraint penalties
        for (i, j), val in quad_coord.items():
            u, v = min(i, j), max(i, j)
            Q[u, v] += val

        for (i, j), val in penalties["quadratic_penalties"].items():
            u, v = min(i, j), max(i, j)
            Q[u, v] += val

        # Create dictionary format for quantum mapping: {(i, j): weight}
        qubo_dict: Dict[Tuple[int, int], float] = {}
        for i in range(n):
            for j in range(i, n):
                if abs(Q[i, j]) > 1e-5:
                    qubo_dict[(i, j)] = round(float(Q[i, j]), 4)

        # Formulate human-readable mathematical objective representation
        equation_terms = []
        for i in range(n):
            if abs(Q[i, i]) > 1e-4:
                equation_terms.append(f"{Q[i, i]:+.2f} x_{{{var_names[i]}}}")
        for i in range(n):
            for j in range(i + 1, n):
                if abs(Q[i, j]) > 1e-4:
                    equation_terms.append(f"{Q[i, j]:+.2f} x_{{{var_names[i]}}} x_{{{var_names[j]}}}")

        equation_str = " ".join(equation_terms) if equation_terms else "0.0"

        return {
            "matrix": Q,
            "qubo_dict": qubo_dict,
            "variables": var_names,
            "variable_meta": var_meta,
            "dimension": n,
            "equation_latex": f"\\min_x \\; x^T Q x = {equation_str}",
            "linear_traffic": linear_traffic.tolist(),
            "penalty_summary": penalties["penalty_breakdown"],
        }
