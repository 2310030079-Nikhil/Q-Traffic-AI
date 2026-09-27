"""
Complete AQSA Pipeline Orchestrator.
Executes the closed-loop AI -> AQSA Priority -> Variable Selection -> Dynamic QUBO
-> Ising -> QAOA -> Feasibility Decoder -> Signal Timing Plan.
"""

from typing import Dict, List, Any, Optional
import numpy as np
import time

from src.ai.predictor import TrafficPredictor
from src.aqsa.priority import SignalPriorityScorer
from src.aqsa.variable_selector import AdaptiveVariableSelector
from src.aqsa.qubo_builder import DynamicQUBOBuilder
from src.quantum.qubo_to_ising import QUBOToIsingConverter
from src.quantum.qaoa import QAOAOptimizer
from src.quantum.simulator import QuantumSimulator
from src.quantum.decoder import FeasibilityAwareDecoder


class AQSAPipeline:
    """
    Main AQSA Framework Controller orchestrating the hybrid AI-Quantum workflow.
    """

    def __init__(
        self,
        predictor: Optional[TrafficPredictor] = None,
        threshold: float = 0.55,
        qubit_budget: int = 6,
        qaoa_depth: int = 1,
        shots: int = 512,
        optimizer: str = "COBYLA",
    ):
        self.predictor = predictor
        self.threshold = threshold
        self.qubit_budget = qubit_budget
        self.qaoa_depth = qaoa_depth
        self.shots = shots
        self.optimizer = optimizer

        # Pipeline sub-components
        self.priority_scorer = SignalPriorityScorer()
        self.variable_selector = AdaptiveVariableSelector(
            threshold=threshold,
            qubit_budget=qubit_budget,
            variables_per_intersection=2,
        )
        self.qubo_builder = DynamicQUBOBuilder()
        self.qaoa_optimizer = QAOAOptimizer(p_depth=qaoa_depth, optimizer=optimizer, maxiter=25)
        self.simulator = QuantumSimulator()
        self.decoder = FeasibilityAwareDecoder()

    def run(
        self,
        traffic_state: Dict[str, Any],
        threshold: Optional[float] = None,
        qubit_budget: Optional[int] = None,
        qaoa_depth: Optional[int] = None,
        shots: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Execute full AQSA optimization pass given current simulation state.
        """
        t0 = time.time()

        tau = threshold if threshold is not None else self.threshold
        budget = qubit_budget if qubit_budget is not None else self.qubit_budget
        p_depth = qaoa_depth if qaoa_depth is not None else self.qaoa_depth
        num_shots = shots if shots is not None else self.shots

        intersections = traffic_state.get("intersections", {})

        # Step 1: AI Traffic Prediction & Uncertainty Estimation
        predictions: Dict[str, Dict[str, Any]] = {}
        uncertainties: Dict[str, Dict[str, Any]] = {}

        for node_id, node_data in intersections.items():
            if self.predictor and self.predictor.is_trained:
                feat = {
                    "time_sin": np.sin(2 * np.pi * (traffic_state.get("timestamp", 0) % 3600) / 3600.0),
                    "time_cos": np.cos(2 * np.pi * (traffic_state.get("timestamp", 0) % 3600) / 3600.0),
                    "volume": node_data.get("volume", 30),
                    "queue_length": node_data.get("queue_length", 10),
                    "avg_waiting_time": node_data.get("avg_waiting_time", 15.0),
                    "occupancy": node_data.get("occupancy", 0.3),
                    "density": node_data.get("density", 25.0),
                    "avg_speed": node_data.get("avg_speed", 12.0),
                    "congestion_index": node_data.get("congestion_index", 0.3),
                    "volume_lag1": node_data.get("volume", 30),
                    "queue_length_lag1": node_data.get("queue_length", 10),
                    "congestion_index_lag1": node_data.get("congestion_index", 0.3),
                    f"node_{node_id}": 1.0,
                }
                pred_out = self.predictor.predict_single(feat)
                predictions[node_id] = pred_out
                uncertainties[node_id] = {
                    "normalized_uncertainty": pred_out.get("target_volume", {}).get("normalized_uncertainty", 0.15),
                    "confidence_margin": pred_out.get("target_volume", {}).get("confidence_margin", 4.0),
                }
            else:
                # Baseline heuristic estimation if model not yet trained
                vol = node_data.get("volume", 30)
                unc = min(0.85, max(0.1, (node_data.get("queue_length", 5) / 50.0) * 0.4 + 0.1))
                predictions[node_id] = {
                    "target_volume": {"prediction": vol * 1.05, "confidence_margin": 4.5, "normalized_uncertainty": unc},
                    "target_queue": {"prediction": node_data.get("queue_length", 10) * 1.05},
                    "target_congestion": {"prediction": node_data.get("congestion_index", 0.3)},
                }
                uncertainties[node_id] = {
                    "normalized_uncertainty": unc,
                    "confidence_margin": 4.5,
                }

        # Step 2: AQSA Signal Priority Scoring
        priorities = self.priority_scorer.compute_priorities(intersections, uncertainties)
        adapted_weights = self.priority_scorer.get_weights_dict()

        # Step 3: Adaptive Variable Selection
        selection_result = self.variable_selector.select_variables(
            priorities=priorities,
            threshold=tau,
            qubit_budget=budget,
        )

        num_qubits = selection_result["num_qubits"]

        # Step 4: Dynamic QUBO Generation & Adaptive Penalties
        qubo_result = self.qubo_builder.build_qubo(
            selection_result=selection_result,
            traffic_states=intersections,
            predictions=predictions,
            priorities=priorities,
        )

        # Step 5: Convert QUBO to Ising Hamiltonian
        ising_result = QUBOToIsingConverter.convert(
            qubo_matrix=qubo_result["matrix"],
            var_names=qubo_result["variables"],
        )

        # Step 6: QAOA Optimization & Quantum Simulation
        self.qaoa_optimizer.p_depth = p_depth
        qaoa_result = self.qaoa_optimizer.optimize(
            cost_operator=ising_result["pauli_op"],
            num_qubits=num_qubits,
        )

        # Step 7: Sample Circuit using Quantum Simulator
        measurement_result = self.simulator.sample_circuit(
            circuit=qaoa_result["optimal_circuit"],
            shots=num_shots,
        )

        # Step 8: Feasibility-Aware Decoding & Signal Plan Generation
        decode_result = self.decoder.decode_and_select(
            measurement_results=measurement_result,
            qubo_matrix=qubo_result["matrix"],
            selection_result=selection_result,
            traffic_states=intersections,
            priorities=priorities,
        )

        elapsed_ms = round((time.time() - t0) * 1000.0, 1)

        return {
            "execution_time_ms": elapsed_ms,
            "timestamp": traffic_state.get("timestamp", 0),
            "predictions": predictions,
            "uncertainties": uncertainties,
            "adapted_weights": adapted_weights,
            "priorities": priorities,
            "selection": selection_result,
            "qubo": qubo_result,
            "ising": ising_result,
            "qaoa": qaoa_result,
            "measurements": measurement_result,
            "decoding": decode_result,
            "signal_plan": decode_result["signal_plan"],
        }
