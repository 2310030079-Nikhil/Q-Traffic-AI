"""
Evaluation metrics suite for traffic and quantum optimization performance.
"""

from typing import Dict, List, Any
import numpy as np


class PerformanceMetrics:
    """
    Computes traffic performance, quantum circuit complexity, and optimization fidelity metrics.
    """

    @staticmethod
    def evaluate_traffic_impact(
        initial_state: Dict[str, Any],
        subsequent_state: Dict[str, Any],
        signal_plan: Dict[str, Any],
        exec_time_ms: float = 0.0,
        qubits: int = 0,
        depth: int = 0,
        violations: int = 0,
        feasibility_pct: float = 100.0,
        objective_val: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Calculates delta in queue lengths, waiting times, congestion scores, and throughput.
        """
        init_nodes = initial_state.get("intersections", {})
        sub_nodes = subsequent_state.get("intersections", {})

        waits_sub = [n.get("avg_waiting_time", 0.0) for n in sub_nodes.values()]
        queues_sub = [n.get("queue_length", 0) for n in sub_nodes.values()]

        avg_wait = float(np.mean(waits_sub)) if waits_sub else 0.0
        max_wait = float(np.max(waits_sub)) if waits_sub else 0.0
        avg_queue = float(np.mean(queues_sub)) if queues_sub else 0.0
        max_queue = int(np.max(queues_sub)) if queues_sub else 0

        congestion_scores = [n.get("congestion_index", 0.0) for n in sub_nodes.values()]
        mean_congestion = float(np.mean(congestion_scores)) if congestion_scores else 0.0

        throughput = subsequent_state.get("throughput_veh_per_min", 25.0)

        return {
            "avg_waiting_time_sec": round(avg_wait, 1),
            "max_waiting_time_sec": round(max_wait, 1),
            "avg_queue_length_veh": round(avg_queue, 1),
            "max_queue_length_veh": max_queue,
            "congestion_score": round(mean_congestion, 3),
            "throughput_veh_per_min": throughput,
            "objective_value": round(objective_val, 4),
            "constraint_violations": violations,
            "computational_time_ms": round(exec_time_ms, 2),
            "quantum_circuit_depth": depth,
            "number_of_qubits": qubits,
            "solution_feasibility_pct": round(feasibility_pct, 1),
        }
