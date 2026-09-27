"""
Baseline 1: Pre-timed Fixed Signal Controller.
Allocates constant, static green split to all approaches regardless of real-time queues.
"""

from typing import Dict, Any


class FixedSignalController:
    """
    Standard pre-timed signal controller allocating fixed cycle splits.
    """

    def __init__(self, default_green_ns: float = 27.0, default_green_ew: float = 27.0):
        self.default_green_ns = default_green_ns
        self.default_green_ew = default_green_ew

    def optimize(self, traffic_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns static fixed-duration signal plan.
        """
        intersections = traffic_state.get("intersections", {})
        signal_plan: Dict[str, Dict[str, float]] = {}

        for node_id in intersections.keys():
            signal_plan[node_id] = {
                "green_ns": self.default_green_ns,
                "green_ew": self.default_green_ew,
                "allocated_by": "FIXED_TIME",
            }

        return {
            "name": "Fixed-Time Signal",
            "signal_plan": signal_plan,
            "execution_time_ms": 0.2,
            "active_qubits": 0,
            "circuit_depth": 0,
            "constraint_violations": 0,
            "feasibility_rate_pct": 100.0,
        }
