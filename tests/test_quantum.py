"""
Unit tests for Quantum Transformation, QAOA, Simulator, and Decoder.
"""

import pytest
import numpy as np
from src.quantum.qubo_to_ising import QUBOToIsingConverter
from src.quantum.qaoa import QAOAOptimizer, QAOACircuitBuilder
from src.quantum.simulator import QuantumSimulator
from src.quantum.decoder import FeasibilityAwareDecoder


def test_qubo_to_ising_conversion():
    # 2-variable toy QUBO: -2*x0 - 3*x1 + 4*x0*x1
    Q = np.array([
        [-2.0, 4.0],
        [0.0, -3.0],
    ])
    ising = QUBOToIsingConverter.convert(Q, var_names=["x0", "x1"])
    assert ising["num_qubits"] == 2
    assert ising["pauli_op"].num_qubits == 2
    assert "x0" in ising["linear_h"]
    assert ("x0", "x1") in ising["coupling_J"]


def test_qaoa_circuit_and_simulation():
    Q = np.array([
        [-2.0, 5.0],
        [0.0, -2.0],
    ])
    ising = QUBOToIsingConverter.convert(Q, var_names=["x0", "x1"])
    opt = QAOAOptimizer(p_depth=1, maxiter=15)
    res = opt.optimize(cost_operator=ising["pauli_op"], num_qubits=2)

    assert "optimal_circuit" in res
    assert res["num_qubits"] == 2
    assert len(res["convergence_history"]) > 0

    sim = QuantumSimulator()
    meas = sim.sample_circuit(res["optimal_circuit"], shots=256)
    assert meas["shots"] == 256
    assert len(meas["probabilities"]) > 0


def test_feasibility_decoder():
    selection_res = {
        "quantum_variables": ["A_phase_NS", "A_phase_EW"],
        "variable_meta": {
            "A_phase_NS": {"intersection_id": "A", "phase": "NS"},
            "A_phase_EW": {"intersection_id": "A", "phase": "EW"},
        },
    }
    qubo_mat = np.array([
        [-5.0, 15.0],
        [0.0, -3.0],
    ])
    meas_res = {
        "probabilities": {
            "11": 0.50,  # Infeasible conflict!
            "10": 0.35,  # Feasible
            "01": 0.15,  # Feasible
        }
    }
    states = {"A": {"queue_length": 20, "avg_waiting_time": 25.0}}
    priorities = {"A": {"priority_score": 0.8}}

    decoder = FeasibilityAwareDecoder()
    dec_out = decoder.decode_and_select(
        measurement_results=meas_res,
        qubo_matrix=qubo_mat,
        selection_result=selection_res,
        traffic_states=states,
        priorities=priorities,
    )

    # Must select feasible solution (10 or 01), not the highest probability conflicting 11!
    best = dec_out["selected_solution"]
    assert best["is_feasible"] is True
    assert best["bitstring"] in ("10", "01")
    assert best["bitstring"] != "11"
