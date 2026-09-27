"""
Unit tests for AQSA Priority Scoring, Variable Selection, Dynamic QUBO, and Pipeline.
"""

import pytest
from src.traffic.simulator import TrafficSimulator
from src.aqsa.priority import SignalPriorityScorer
from src.aqsa.variable_selector import AdaptiveVariableSelector
from src.aqsa.qubo_builder import DynamicQUBOBuilder
from src.aqsa.aqsa_pipeline import AQSAPipeline


def test_aqsa_priority_scoring():
    sim = TrafficSimulator(num_intersections=4, scenario="morning_peak")
    state = sim.step()

    scorer = SignalPriorityScorer()
    uncs = {node: {"normalized_uncertainty": 0.2, "confidence_margin": 4.0} for node in state["intersections"]}
    priorities = scorer.compute_priorities(state["intersections"], uncs)

    assert len(priorities) == 4
    for node, p in priorities.items():
        assert 0.0 <= p["priority_score"] <= 1.0


def test_aqsa_variable_selection():
    priorities = {
        "A": {"intersection_id": "A", "priority_score": 0.92},
        "B": {"intersection_id": "B", "priority_score": 0.75},
        "C": {"intersection_id": "C", "priority_score": 0.25},
        "D": {"intersection_id": "D", "priority_score": 0.82},
    }

    selector = AdaptiveVariableSelector(threshold=0.60, qubit_budget=6, variables_per_intersection=2)
    res = selector.select_variables(priorities)

    assert "A" in res["selected_node_ids"]
    assert "D" in res["selected_node_ids"]
    assert "C" not in res["selected_node_ids"]
    assert res["num_qubits"] <= 6
    assert len(res["quantum_variables"]) == res["num_qubits"]


def test_full_aqsa_pipeline_execution():
    sim = TrafficSimulator(num_intersections=4, scenario="morning_peak")
    state = sim.step()

    pipeline = AQSAPipeline(threshold=0.50, qubit_budget=4, qaoa_depth=1, shots=256)
    out = pipeline.run(state)

    assert "selection" in out
    assert "qubo" in out
    assert "qaoa" in out
    assert "decoding" in out
    assert "signal_plan" in out
    assert out["decoding"]["selected_solution"]["is_feasible"] is True
