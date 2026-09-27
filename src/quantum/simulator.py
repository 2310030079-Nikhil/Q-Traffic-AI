"""
Local quantum simulation execution using Qiskit Aer and Statevector.
"""

from typing import Dict, Any, List
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit.quantum_info import Statevector


class QuantumSimulator:
    """
    Simulates measurement sampling of optimized QAOA quantum circuits.
    """

    def __init__(self, backend_type: str = "aer"):
        self.backend_type = backend_type
        self.simulator = AerSimulator()

    def sample_circuit(
        self,
        circuit: QuantumCircuit,
        shots: int = 512,
        seed: int = 42,
    ) -> Dict[str, Any]:
        """
        Execute measurement simulation and return bitstring probability distribution.
        """
        n = circuit.num_qubits

        # Fast exact statevector sampling
        sv = Statevector(circuit)
        exact_probs = sv.probabilities_dict()

        # Simulate shot measurement sampling from exact probabilities
        bitstrings = list(exact_probs.keys())
        probs = np.array(list(exact_probs.values()))
        probs = probs / np.sum(probs)  # normalize

        np.random.seed(seed)
        sampled_indices = np.random.choice(len(bitstrings), size=shots, p=probs)
        unique_idx, counts = np.unique(sampled_indices, return_counts=True)

        measurement_counts: Dict[str, int] = {}
        probabilities: Dict[str, float] = {}

        for u_idx, count in zip(unique_idx, counts):
            b_str = bitstrings[u_idx]
            measurement_counts[b_str] = int(count)
            probabilities[b_str] = round(float(count / shots), 4)

        # Sort bitstrings descending by probability
        sorted_probs = dict(sorted(probabilities.items(), key=lambda x: x[1], reverse=True))

        return {
            "shots": shots,
            "counts": measurement_counts,
            "probabilities": sorted_probs,
            "most_probable_bitstring": next(iter(sorted_probs)),
            "num_unique_solutions": len(sorted_probs),
        }
