"""
Parameterized QAOA circuit generator and variational parameter optimizer.
"""

from typing import Dict, List, Tuple, Any, Callable
import numpy as np
from scipy.optimize import minimize
from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector
from qiskit.quantum_info import SparsePauliOp, Statevector


class QAOACircuitBuilder:
    """
    Constructs parameterized QAOA quantum circuits for Ising cost Hamiltonians.
    """

    def __init__(self, num_qubits: int, p_depth: int = 1):
        self.num_qubits = num_qubits
        self.p_depth = p_depth

    def build_circuit(self, cost_operator: SparsePauliOp) -> Tuple[QuantumCircuit, ParameterVector, ParameterVector]:
        """
        Creates variational QAOA ansatz: |psi(gamma, beta)> = U(B, beta_p) U(C, gamma_p) ... |+>^n
        """
        n = self.num_qubits
        p = self.p_depth

        gamma = ParameterVector("gamma", p)
        beta = ParameterVector("beta", p)

        qc = QuantumCircuit(n)
        # Uniform superposition |+>^n
        qc.h(range(n))

        op_list = cost_operator.to_list()

        for step in range(p):
            # Cost Hamiltonian unitary: e^{-i gamma H_C}
            for pauli_str, coeff in op_list:
                weight = float(coeff.real)
                z_indices = [n - 1 - idx for idx, char in enumerate(pauli_str) if char == "Z"]

                if len(z_indices) == 1:
                    qc.rz(2.0 * gamma[step] * weight, z_indices[0])
                elif len(z_indices) == 2:
                    qc.rzz(2.0 * gamma[step] * weight, z_indices[0], z_indices[1])

            # Transverse field mixer unitary: e^{-i beta H_M}
            for q in range(n):
                qc.rx(2.0 * beta[step], q)

        return qc, gamma, beta


class QAOAOptimizer:
    """
    Variational quantum eigensolver loop for QAOA using classical optimizers (COBYLA/SPSA).
    """

    def __init__(
        self,
        p_depth: int = 1,
        optimizer: str = "COBYLA",
        maxiter: int = 35,
    ):
        self.p_depth = p_depth
        self.optimizer = optimizer
        self.maxiter = maxiter
        self.history: List[Dict[str, Any]] = []

    def optimize(
        self,
        cost_operator: SparsePauliOp,
        num_qubits: int,
    ) -> Dict[str, Any]:
        """
        Run classical optimization to find optimal (gamma, beta) angles minimizing <H_C>.
        """
        builder = QAOACircuitBuilder(num_qubits=num_qubits, p_depth=self.p_depth)
        circuit, gamma_vec, beta_vec = builder.build_circuit(cost_operator)

        self.history = []

        # Loss function for classical optimizer
        def objective(params: np.ndarray) -> float:
            gammas = params[: self.p_depth]
            betas = params[self.p_depth :]

            param_binding = {}
            for i in range(self.p_depth):
                param_binding[gamma_vec[i]] = gammas[i]
                param_binding[beta_vec[i]] = betas[i]

            bound_qc = circuit.assign_parameters(param_binding)
            sv = Statevector(bound_qc)
            energy = float(sv.expectation_value(cost_operator).real)

            step_idx = len(self.history)
            self.history.append({
                "iteration": step_idx,
                "cost": round(energy, 4),
                "gammas": [round(float(g), 3) for g in gammas],
                "betas": [round(float(b), 3) for b in betas],
            })
            return energy

        # Initial parameter guess
        x0 = np.concatenate([
            np.linspace(0.1, 0.4, self.p_depth),
            np.linspace(0.4, 0.1, self.p_depth),
        ])

        opt_result = minimize(
            objective,
            x0=x0,
            method="COBYLA",
            options={"maxiter": self.maxiter, "rhobeg": 0.5},
        )

        opt_gammas = opt_result.x[: self.p_depth].tolist()
        opt_betas = opt_result.x[self.p_depth :].tolist()

        # Bind optimal parameters to circuit
        optimal_binding = {}
        for i in range(self.p_depth):
            optimal_binding[gamma_vec[i]] = opt_gammas[i]
            optimal_binding[beta_vec[i]] = opt_betas[i]

        optimal_circuit = circuit.assign_parameters(optimal_binding)

        return {
            "optimal_parameters": {
                "gamma": [round(g, 4) for g in opt_gammas],
                "beta": [round(b, 4) for b in opt_betas],
            },
            "optimal_cost": round(float(opt_result.fun), 4),
            "convergence_history": self.history,
            "optimal_circuit": optimal_circuit,
            "circuit_depth": optimal_circuit.depth(),
            "gate_counts": optimal_circuit.count_ops(),
            "num_qubits": num_qubits,
        }
