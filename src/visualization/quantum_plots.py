"""
Quantum visualization suite: QUBO heatmaps, QAOA convergence traces,
bitstring measurement probability distributions, and circuit representations.
"""

from typing import Dict, List, Any
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from qiskit import QuantumCircuit


class QuantumPlotVisualizer:
    """
    Renders high-fidelity visualizations for quantum optimization results.
    """

    @staticmethod
    def plot_qubo_heatmap(qubo_result: Dict[str, Any]) -> go.Figure:
        """
        Interactive annotated heatmap of the dynamically constructed QUBO matrix.
        """
        matrix = qubo_result.get("matrix", np.zeros((1, 1)))
        var_names = qubo_result.get("variables", ["q0"])
        n = len(var_names)

        # Build custom text labels
        text_vals = []
        for i in range(n):
            row = []
            for j in range(n):
                val = matrix[i, j]
                if abs(val) > 1e-4:
                    row.append(f"{val:.2f}")
                else:
                    row.append("")
            text_vals.append(row)

        fig = go.Figure(data=go.Heatmap(
            z=matrix,
            x=var_names,
            y=var_names,
            text=text_vals,
            texttemplate="%{text}",
            textfont=dict(size=12, color="#ffffff"),
            colorscale=[
                [0.0, "#00f2fe"],   # Cyan (negative rewards)
                [0.45, "#1e293b"],  # Dark Slate (neutral / zero)
                [1.0, "#ff1744"],   # Crimson Red (penalties)
            ],
            colorbar=dict(
                title=dict(text="Coefficient", font=dict(color="#94a3b8")),
                tickfont=dict(color="#94a3b8"),
            ),
        ))

        fig.update_layout(
            title=dict(
                text=f"<b>Dynamic QUBO Matrix Q ({n}×{n})</b>",
                font=dict(size=16, color="#f8fafc"),
            ),
            paper_bgcolor="#090d16",
            plot_bgcolor="#090d16",
            xaxis=dict(tickfont=dict(color="#cbd5e1"), tickangle=-30),
            yaxis=dict(tickfont=dict(color="#cbd5e1"), autorange="reversed"),
            margin=dict(l=40, r=40, t=50, b=40),
            height=420,
        )
        return fig

    @staticmethod
    def plot_convergence_history(history: List[Dict[str, Any]]) -> go.Figure:
        """
        Plots classical optimizer convergence: Iteration vs Energy expectation <H_C>.
        """
        if not history:
            fig = go.Figure()
            fig.update_layout(paper_bgcolor="#090d16", plot_bgcolor="#090d16")
            return fig

        iterations = [h["iteration"] for h in history]
        costs = [h["cost"] for h in history]

        fig = go.Figure()

        # Convergence line trace
        fig.add_trace(go.Scatter(
            x=iterations,
            y=costs,
            mode="lines+markers",
            line=dict(color="#00f2fe", width=2.5),
            marker=dict(size=7, color="#38bdf8", symbol="circle"),
            name="QAOA Expectation <H_C>",
        ))

        # Best minimum point
        min_idx = int(np.argmin(costs))
        fig.add_trace(go.Scatter(
            x=[iterations[min_idx]],
            y=[costs[min_idx]],
            mode="markers",
            marker=dict(size=14, color="#00e676", symbol="star", line=dict(color="#ffffff", width=2)),
            name=f"Optimal Min ({costs[min_idx]:.2f})",
        ))

        fig.update_layout(
            title=dict(
                text="<b>QAOA Parameter Optimization Trace (COBYLA)</b>",
                font=dict(size=15, color="#f8fafc"),
            ),
            paper_bgcolor="#090d16",
            plot_bgcolor="#090d16",
            xaxis=dict(
                title=dict(text="Evaluation Iteration", font=dict(color="#94a3b8")),
                tickfont=dict(color="#94a3b8"),
                gridcolor="#1e293b",
            ),
            yaxis=dict(
                title=dict(text="Hamiltonian Expectation Energy", font=dict(color="#94a3b8")),
                tickfont=dict(color="#94a3b8"),
                gridcolor="#1e293b",
            ),
            legend=dict(font=dict(color="#cbd5e1")),
            margin=dict(l=40, r=40, t=50, b=40),
            height=350,
        )
        return fig

    @staticmethod
    def plot_measurement_distribution(
        evaluated_solutions: List[Dict[str, Any]],
        selected_bitstring: str = "",
    ) -> go.Figure:
        """
        Plots measured bitstring distribution distinguishing feasible vs infeasible candidates.
        """
        # Limit to top 15 bitstrings for visual clarity
        top_sols = sorted(evaluated_solutions, key=lambda s: s["probability"], reverse=True)[:14]

        bitstrings = [s["bitstring"] for s in top_sols]
        probs = [s["probability"] * 100.0 for s in top_sols]
        colors = []

        for s in top_sols:
            b = s["bitstring"]
            if b == selected_bitstring:
                colors.append("#00e676")  # Vibrant Green for Selected Optimal Feasible
            elif s["is_feasible"]:
                colors.append("#00f2fe")  # Cyan for other feasible solutions
            else:
                colors.append("#ef4444")  # Red for infeasible constraint violations

        fig = go.Figure(data=go.Bar(
            x=bitstrings,
            y=probs,
            marker=dict(color=colors, line=dict(color="#0f172a", width=1.5)),
            text=[f"{p:.1f}%" for p in probs],
            textposition="outside",
            textfont=dict(color="#cbd5e1", size=11),
            hovertext=[
                f"<b>Bitstring: {s['bitstring']}</b><br>"
                f"Status: <b>{'FEASIBLE' if s['is_feasible'] else 'INFEASIBLE (VIOLATION)'}</b><br>"
                f"Probability: <b>{s['probability']*100:.1f}%</b><br>"
                f"QUBO Energy: <b>{s['qubo_objective']:.2f}</b><br>"
                f"Queue Reduction: <b>{s['queue_reduction_veh']} veh</b>"
                for s in top_sols
            ],
            hoverinfo="text",
        ))

        fig.update_layout(
            title=dict(
                text="<b>Quantum Measurement Distribution & Feasibility Analysis</b>",
                font=dict(size=15, color="#f8fafc"),
            ),
            paper_bgcolor="#090d16",
            plot_bgcolor="#090d16",
            xaxis=dict(
                title=dict(text="Measured Bitstring |x⟩", font=dict(color="#94a3b8")),
                tickfont=dict(color="#cbd5e1"),
                tickangle=-30,
            ),
            yaxis=dict(
                title=dict(text="Sampling Probability (%)", font=dict(color="#94a3b8")),
                tickfont=dict(color="#94a3b8"),
                gridcolor="#1e293b",
            ),
            margin=dict(l=40, r=40, t=50, b=40),
            height=370,
        )
        return fig

    @staticmethod
    def get_circuit_ascii(circuit: QuantumCircuit) -> str:
        """Return formatted text diagram of QAOA circuit."""
        try:
            return circuit.draw(output="text").single_string()
        except Exception:
            return str(circuit)
