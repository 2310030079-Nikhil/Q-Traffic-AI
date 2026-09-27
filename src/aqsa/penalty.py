"""
AQSA Stage 4: Adaptive Penalty Mechanism.
Computes mathematically justified, priority-weighted constraint penalties for QUBO formulation.
"""

from typing import Dict, List, Any, Tuple
import numpy as np


class AdaptivePenaltyManager:
    """
    Computes priority-adapted constraint penalties for mutually exclusive phases
    and minimum phase activation constraints in traffic QUBO.
    """

    def __init__(self, base_penalty: float = 8.0, scaling_factor: float = 1.5):
        self.base_penalty = base_penalty
        self.scaling_factor = scaling_factor

    def compute_penalty_weight(self, priority_score: float) -> float:
        """
        Adaptive penalty formula:
        Lambda_i = BasePenalty * (1.0 + ScalingFactor * Priority_i)
        
        High-priority bottlenecks incur stricter penalties for constraint violations,
        preventing phase gridlocks and unsafe concurrent green intervals.
        """
        return float(self.base_penalty * (1.0 + self.scaling_factor * max(0.0, priority_score)))

    def get_penalties_for_variables(
        self,
        variable_meta: Dict[str, Dict[str, Any]],
        priorities: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Computes the adaptive penalty terms to be added to QUBO matrix.
        Returns:
            linear_penalties: {var_idx: penalty_val}
            quadratic_penalties: {(var_i, var_j): penalty_val}
            penalty_summary: explanation metadata
        """
        var_list = list(variable_meta.keys())
        var_to_idx = {name: idx for idx, name in enumerate(var_list)}

        linear_penalties: Dict[int, float] = {i: 0.0 for i in range(len(var_list))}
        quadratic_penalties: Dict[Tuple[int, int], float] = {}
        penalty_breakdown: List[Dict[str, Any]] = []

        # Group variables by intersection
        node_vars: Dict[str, List[str]] = {}
        for var_name, meta in variable_meta.items():
            node_id = meta["intersection_id"]
            node_vars.setdefault(node_id, []).append(var_name)

        for node_id, vars_in_node in node_vars.items():
            p_score = priorities.get(node_id, {}).get("priority_score", 0.5)
            lam = self.compute_penalty_weight(p_score)

            if len(vars_in_node) == 2:
                v_ns, v_ew = vars_in_node[0], vars_in_node[1]
                idx_ns = var_to_idx[v_ns]
                idx_ew = var_to_idx[v_ew]

                # 1. Mutual Exclusion Penalty: Phase NS and Phase EW cannot both be 1
                # Penalty: Lam * x_NS * x_EW
                pair = (min(idx_ns, idx_ew), max(idx_ns, idx_ew))
                quadratic_penalties[pair] = quadratic_penalties.get(pair, 0.0) + (1.8 * lam)

                # 2. Minimum Allocation Penalty: At least one phase must receive active green:
                # Formulation: (1 - x_NS - x_EW)^2 = 1 - 2*x_NS - 2*x_EW + x_NS^2 + 2*x_NS*x_EW + x_EW^2
                # Since x^2 = x: = 1 - x_NS - x_EW + 2*x_NS*x_EW
                # Adding weight: -0.6 * lam for linear terms, +1.2 * lam for quadratic term
                linear_penalties[idx_ns] -= 0.6 * lam
                linear_penalties[idx_ew] -= 0.6 * lam
                quadratic_penalties[pair] += 1.2 * lam

                penalty_breakdown.append({
                    "intersection_id": node_id,
                    "priority_score": round(p_score, 3),
                    "adaptive_lambda": round(lam, 2),
                    "variables": [v_ns, v_ew],
                    "constraint": "Mutually Exclusive Green (x_NS * x_EW = 0) + Min Green Requirement",
                    "quadratic_term": round(3.0 * lam, 2),
                })

        return {
            "linear_penalties": linear_penalties,
            "quadratic_penalties": quadratic_penalties,
            "penalty_breakdown": penalty_breakdown,
        }
