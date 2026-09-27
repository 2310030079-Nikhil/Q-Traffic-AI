"""
AQSA Stage 3: Adaptive Quantum Variable Selection.
Filters critical intersections by priority score and maps them to quantum variables
within a designated qubit budget.
"""

from typing import Dict, List, Any, Tuple


class AdaptiveVariableSelector:
    """
    Selects high-priority intersections exceeding the AQSA threshold and maps them
    into quantum decision variables under a strict qubit budget.
    """

    def __init__(
        self,
        threshold: float = 0.55,
        qubit_budget: int = 6,
        variables_per_intersection: int = 2,
    ):
        self.threshold = threshold
        self.qubit_budget = qubit_budget
        self.variables_per_intersection = variables_per_intersection

    def select_variables(
        self,
        priorities: Dict[str, Dict[str, Any]],
        threshold: float = None,
        qubit_budget: int = None,
    ) -> Dict[str, Any]:
        """
        Rank intersections, apply priority cutoff, and construct quantum variable index.
        """
        tau = threshold if threshold is not None else self.threshold
        budget = qubit_budget if qubit_budget is not None else self.qubit_budget

        # Sort intersections descending by priority score
        ranked = sorted(
            priorities.values(),
            key=lambda x: x["priority_score"],
            reverse=True,
        )

        max_nodes = budget // self.variables_per_intersection

        selected_nodes: List[Dict[str, Any]] = []
        skipped_nodes: List[Dict[str, Any]] = []

        for item in ranked:
            score = item["priority_score"]
            node_id = item["intersection_id"]

            if score >= tau and len(selected_nodes) < max_nodes:
                selected_nodes.append({
                    "intersection_id": node_id,
                    "priority_score": score,
                    "reason": f"Priority {score:.3f} >= threshold {tau:.2f}. Selected for quantum allocation.",
                })
            else:
                reason = (
                    f"Qubit budget reached (max {max_nodes} nodes)."
                    if len(selected_nodes) >= max_nodes
                    else f"Priority {score:.3f} < threshold {tau:.2f}. Handled by classical heuristic."
                )
                skipped_nodes.append({
                    "intersection_id": node_id,
                    "priority_score": score,
                    "reason": reason,
                })

        # Safeguard: Ensure at least 1 intersection is selected if network exists
        if not selected_nodes and ranked:
            top_node = ranked[0]
            selected_nodes.append({
                "intersection_id": top_node["intersection_id"],
                "priority_score": top_node["priority_score"],
                "reason": "Top bottleneck selected to guarantee adaptive quantum coverage.",
            })
            if skipped_nodes:
                skipped_nodes.pop(0)

        # Build quantum variable list and mapping
        quantum_variables: List[str] = []
        variable_meta: Dict[str, Dict[str, Any]] = {}

        for node_info in selected_nodes:
            n_id = node_info["intersection_id"]
            if self.variables_per_intersection == 2:
                var_ns = f"{n_id}_phase_NS"
                var_ew = f"{n_id}_phase_EW"
                quantum_variables.extend([var_ns, var_ew])
                variable_meta[var_ns] = {
                    "intersection_id": n_id,
                    "phase": "NS",
                    "description": f"Extended green allocation for North-South approach at Node {n_id}",
                }
                variable_meta[var_ew] = {
                    "intersection_id": n_id,
                    "phase": "EW",
                    "description": f"Extended green allocation for East-West approach at Node {n_id}",
                }
            else:
                var_name = f"{n_id}_priority_phase"
                quantum_variables.append(var_name)
                variable_meta[var_name] = {
                    "intersection_id": n_id,
                    "phase": "SPLIT",
                    "description": f"Phase balance decision (1: NS dominant, 0: EW dominant) at Node {n_id}",
                }

        num_qubits = len(quantum_variables)

        return {
            "threshold": tau,
            "qubit_budget": budget,
            "selected_nodes": selected_nodes,
            "skipped_nodes": skipped_nodes,
            "selected_node_ids": [n["intersection_id"] for n in selected_nodes],
            "quantum_variables": quantum_variables,
            "variable_meta": variable_meta,
            "num_qubits": num_qubits,
            "reduction_ratio": round(1.0 - (len(selected_nodes) / max(1, len(ranked))), 3),
        }
