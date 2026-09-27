"""
Transformation from QUBO matrix to Ising Hamiltonian formulation and Qiskit SparsePauliOp.
"""

from typing import Dict, List, Tuple, Any
import numpy as np
from qiskit.quantum_info import SparsePauliOp


class QUBOToIsingConverter:
    """
    Converts binary QUBO problem min x^T Q x to Ising spin Hamiltonian:
    H_C = sum_i h_i Z_i + sum_{i<j} J_ij Z_i Z_j + offset
    using substitution x_i = (I - Z_i) / 2.
    """

    @staticmethod
    def convert(
        qubo_matrix: np.ndarray,
        var_names: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Derive Ising coefficients (h, J, offset) and construct Qiskit SparsePauliOp.
        """
        n = qubo_matrix.shape[0]
        if n == 0:
            return {
                "pauli_op": SparsePauliOp.from_list([("I", 0.0)]),
                "linear_h": {},
                "coupling_J": {},
                "offset": 0.0,
                "ising_latex": "H_C = 0",
            }

        # Initialize Ising coefficients
        h = np.zeros(n, dtype=float)
        J = {}
        offset = 0.0

        # Diagonal contributions: Q_ii * (I - Z_i)/2 = (Q_ii / 2)*I - (Q_ii / 2)*Z_i
        for i in range(n):
            q_ii = qubo_matrix[i, i]
            offset += q_ii / 2.0
            h[i] -= q_ii / 2.0

        # Off-diagonal contributions: Q_ij * (I - Z_i)(I - Z_j) / 4
        # = (Q_ij / 4) * [ I - Z_i - Z_j + Z_i Z_j ]
        for i in range(n):
            for j in range(i + 1, n):
                q_ij = qubo_matrix[i, j]
                if abs(q_ij) > 1e-6:
                    quarter = q_ij / 4.0
                    offset += quarter
                    h[i] -= quarter
                    h[j] -= quarter
                    J[(i, j)] = quarter

        # Build Qiskit SparsePauliOp
        pauli_list: List[Tuple[str, complex]] = []

        # Single-qubit Z terms
        for i in range(n):
            if abs(h[i]) > 1e-6:
                # Qiskit qubit 0 is rightmost in Pauli string
                pauli_str = ["I"] * n
                pauli_str[n - 1 - i] = "Z"
                pauli_list.append(("".join(pauli_str), complex(h[i], 0.0)))

        # Two-qubit ZZ coupling terms
        for (i, j), j_val in J.items():
            if abs(j_val) > 1e-6:
                pauli_str = ["I"] * n
                pauli_str[n - 1 - i] = "Z"
                pauli_str[n - 1 - j] = "Z"
                pauli_list.append(("".join(pauli_str), complex(j_val, 0.0)))

        # If empty, add zero-operator
        if not pauli_list:
            pauli_list.append(("I" * n, 0.0))

        operator = SparsePauliOp.from_list(pauli_list)

        # Build LaTeX string for UI display
        latex_terms = []
        names = var_names if var_names else [f"q_{i}" for i in range(n)]
        for i in range(n):
            if abs(h[i]) > 1e-4:
                latex_terms.append(f"{h[i]:+.3f} Z_{{{names[i]}}}")
        for (i, j), j_val in J.items():
            if abs(j_val) > 1e-4:
                latex_terms.append(f"{j_val:+.3f} Z_{{{names[i]}}} Z_{{{names[j]}}}")

        latex_str = f"H_C = {' '.join(latex_terms)} {offset:+.3f} \\mathbb{{I}}"

        return {
            "pauli_op": operator,
            "linear_h": {names[i]: round(float(h[i]), 4) for i in range(n)},
            "coupling_J": {(names[i], names[j]): round(float(val), 4) for (i, j), val in J.items()},
            "offset": round(float(offset), 4),
            "ising_latex": latex_str,
            "num_qubits": n,
        }
