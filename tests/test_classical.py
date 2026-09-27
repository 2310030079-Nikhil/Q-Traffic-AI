"""
Unit tests for Classical Baseline Controllers (Fixed, Greedy, Brute-Force).
"""

import pytest
import numpy as np
from src.traffic.simulator import TrafficSimulator
from src.classical.fixed_signal import FixedSignalController
from src.classical.greedy import GreedySignalController
from src.classical.brute_force import BruteForceOptimizer


def test_fixed_signal():
    sim = TrafficSimulator(num_intersections=4)
    state = sim.step()

    ctrl = FixedSignalController(default_green_ns=26.0, default_green_ew=26.0)
    res = ctrl.optimize(state)

    assert "signal_plan" in res
    assert res["signal_plan"]["A"]["green_ns"] == 26.0


def test_greedy_signal():
    sim = TrafficSimulator(num_intersections=4)
    state = sim.step()

    ctrl = GreedySignalController()
    res = ctrl.optimize(state)

    assert "signal_plan" in res
    assert "A" in res["signal_plan"]
    assert res["signal_plan"]["A"]["green_ns"] > 0
    assert res["signal_plan"]["A"]["green_ew"] > 0


def test_brute_force():
    selection_res = {
        "quantum_variables": ["A_phase_NS", "A_phase_EW"],
        "variable_meta": {
            "A_phase_NS": {"intersection_id": "A", "phase": "NS"},
            "A_phase_EW": {"intersection_id": "A", "phase": "EW"},
        },
    }
    # QUBO: NS is heavily favored (-8 vs -2)
    Q = np.array([
        [-8.0, 20.0],
        [0.0, -2.0],
    ])
    states = {"A": {"queue_length": 25}}
    priorities = {"A": {"priority_score": 0.85}}

    bf = BruteForceOptimizer()
    res = bf.optimize(Q, selection_res, states, priorities)

    assert res["optimal_bitstring"] == "10"
    assert res["feasible_count"] == 2  # '10' and '01' are feasible; '00' and '11' are not
