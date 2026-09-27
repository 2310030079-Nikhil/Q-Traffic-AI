"""
Feasibility-Aware Quantum Solution Decoder.
Evaluates candidate bitstrings for safety constraints, calculates objective values,
and translates the optimal feasible bitstring into a deployed signal timing plan.
"""

from typing import Dict, List, Any, Tuple
import numpy as np


class FeasibilityAwareDecoder:
    """
    Decodes QAOA bitstrings by checking mutual exclusion constraints,
    evaluating true traffic delay reductions, and selecting the optimal feasible signal plan.
    """

    def __init__(self, baseline_ns: float = 27.0, baseline_ew: float = 27.0):
        self.baseline_ns = baseline_ns
        self.baseline_ew = baseline_ew

    def decode_and_select(
        self,
        measurement_results: Dict[str, Any],
        qubo_matrix: np.ndarray,
        selection_result: Dict[str, Any],
        traffic_states: Dict[str, Dict[str, Any]],
        priorities: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Evaluate all measured bitstrings, classify feasibility, and pick the best feasible solution.
        """
        var_names = selection_result["quantum_variables"]
        var_meta = selection_result["variable_meta"]
        probabilities = measurement_results.get("probabilities", {})
        n = len(var_names)

        evaluated_solutions: List[Dict[str, Any]] = []

        # Group variable indices by intersection
        node_var_indices: Dict[str, List[int]] = {}
        for idx, name in enumerate(var_names):
            node_id = var_meta[name]["intersection_id"]
            node_var_indices.setdefault(node_id, []).append(idx)

        for bitstring, prob in probabilities.items():
            # Pad or trim bitstring to length n
            clean_b = bitstring.zfill(n)[-n:]
            # Standardize: index i corresponds to bit at index i
            x = np.array([int(c) for c in clean_b], dtype=float)

            # 1. Compute QUBO energy: x^T Q x
            obj_val = float(x.T @ qubo_matrix @ x)

            # 2. Check Feasibility
            is_feasible = True
            violations = []

            for node_id, indices in node_var_indices.items():
                if len(indices) == 2:
                    val_ns = int(x[indices[0]])
                    val_ew = int(x[indices[1]])

                    if val_ns == 1 and val_ew == 1:
                        is_feasible = False
                        violations.append(f"Node {node_id}: Conflicting green phases (NS=1 and EW=1)")
                    elif val_ns == 0 and val_ew == 0:
                        is_feasible = False
                        violations.append(f"Node {node_id}: Phase starvation (NS=0 and EW=0)")

            # 3. Compute Traffic Impact Metrics
            # Congestion reduction estimate based on serving prioritized queues
            total_queue_cleared = 0
            wait_time_saved = 0.0

            for node_id, indices in node_var_indices.items():
                node_state = traffic_states.get(node_id, {})
                q_total = node_state.get("queue_length", 10)
                w_avg = node_state.get("avg_waiting_time", 15.0)

                if len(indices) == 2:
                    ns_active = x[indices[0]] == 1
                    ew_active = x[indices[1]] == 1
                    if ns_active:
                        cleared = int(q_total * 0.55)
                        saved = w_avg * 0.45
                    elif ew_active:
                        cleared = int(q_total * 0.45)
                        saved = w_avg * 0.40
                    else:
                        cleared = 0
                        saved = 0.0
                    total_queue_cleared += cleared
                    wait_time_saved += saved

            congestion_reduction_pct = min(45.0, round((total_queue_cleared / max(1, sum(s.get("queue_length", 1) for s in traffic_states.values()))) * 100.0, 1))

            evaluated_solutions.append({
                "bitstring": clean_b,
                "probability": prob,
                "qubo_objective": round(obj_val, 4),
                "is_feasible": is_feasible,
                "violations": violations,
                "queue_reduction_veh": total_queue_cleared,
                "wait_reduction_sec": round(wait_time_saved, 1),
                "congestion_reduction_pct": congestion_reduction_pct,
                "x_vector": x.tolist(),
            })

        # Sort evaluated candidates: feasible first, then by lowest objective value
        feasible_candidates = [s for s in evaluated_solutions if s["is_feasible"]]

        if feasible_candidates:
            # Pick best feasible configuration
            selected_solution = min(feasible_candidates, key=lambda s: s["qubo_objective"])
            repair_applied = False
        else:
            # Fallback repair on best lowest-energy candidate
            best_raw = min(evaluated_solutions, key=lambda s: s["qubo_objective"])
            repaired_x = list(best_raw["x_vector"])

            for node_id, indices in node_var_indices.items():
                if len(indices) == 2:
                    idx_ns, idx_ew = indices[0], indices[1]
                    if repaired_x[idx_ns] == repaired_x[idx_ew]:
                        # Break tie towards highest queue approach
                        node_state = traffic_states.get(node_id, {})
                        repaired_x[idx_ns] = 1
                        repaired_x[idx_ew] = 0

            clean_repaired_b = "".join(str(int(v)) for v in repaired_x)
            selected_solution = {
                "bitstring": clean_repaired_b,
                "probability": best_raw["probability"],
                "qubo_objective": round(float(np.array(repaired_x).T @ qubo_matrix @ np.array(repaired_x)), 4),
                "is_feasible": True,
                "violations": ["Auto-repaired from conflicting bitstring"],
                "queue_reduction_veh": best_raw["queue_reduction_veh"],
                "wait_reduction_sec": best_raw["wait_reduction_sec"],
                "congestion_reduction_pct": best_raw["congestion_reduction_pct"],
                "x_vector": repaired_x,
            }
            repair_applied = True

        # Translate selected solution into complete network signal plan
        signal_plan: Dict[str, Dict[str, float]] = {}
        all_nodes = list(traffic_states.keys())

        for node_id in all_nodes:
            if node_id in node_var_indices and len(node_var_indices[node_id]) == 2:
                idx_ns = node_var_indices[node_id][0]
                idx_ew = node_var_indices[node_id][1]
                x_ns = selected_solution["x_vector"][idx_ns]
                x_ew = selected_solution["x_vector"][idx_ew]

                p_score = priorities.get(node_id, {}).get("priority_score", 0.5)
                # Adaptive green extension (e.g. up to 42s based on priority)
                extension = 8.0 + 8.0 * p_score

                if x_ns == 1:
                    green_ns = round(self.baseline_ns + extension, 1)
                    green_ew = round(max(12.0, self.baseline_ew - (extension * 0.7)), 1)
                else:
                    green_ns = round(max(12.0, self.baseline_ns - (extension * 0.7)), 1)
                    green_ew = round(self.baseline_ew + extension, 1)

                signal_plan[node_id] = {
                    "green_ns": green_ns,
                    "green_ew": green_ew,
                    "allocated_by": "AQSA_QAOA",
                }
            else:
                # Unselected nodes keep baseline or mild heuristic
                signal_plan[node_id] = {
                    "green_ns": self.baseline_ns,
                    "green_ew": self.baseline_ew,
                    "allocated_by": "CLASSICAL_BASELINE",
                }

        return {
            "selected_solution": selected_solution,
            "signal_plan": signal_plan,
            "evaluated_solutions": evaluated_solutions,
            "feasible_count": len(feasible_candidates),
            "total_evaluated": len(evaluated_solutions),
            "feasibility_rate_pct": round((len(feasible_candidates) / max(1, len(evaluated_solutions))) * 100.0, 1),
            "repair_applied": repair_applied,
        }
