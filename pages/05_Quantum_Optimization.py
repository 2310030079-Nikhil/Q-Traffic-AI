"""
05_Quantum_Optimization.py: Quantum Command Deck and QAOA Visualizer.
Dynamic QUBO heatmap, Ising Hamiltonian formulation, QAOA circuit, optimizer convergence,
measurement distribution, and feasibility decoding.
"""

import streamlit as st
import pandas as pd
from src.ui_common import apply_theme, render_brand_header, init_session_state, set_flash_message
from src.visualization.quantum_plots import QuantumPlotVisualizer

st.set_page_config(page_title="Quantum Optimization | Q-TrafficAI", page_icon="⚛", layout="wide")
apply_theme()
init_session_state()

render_brand_header(subtitle="Stage 4, 5 & 6: QUBO Assembly, Ising Mapping, and QAOA Quantum Simulation")

latest = st.session_state.latest_result
qubo = latest["qubo"]
ising = latest["ising"]
qaoa = latest["qaoa"]
meas = latest["measurements"]
dec = latest["decoding"]
sol = dec["selected_solution"]

# Quantum Circuit Configuration Sidebar / Expander
with st.expander("⚙️ Quantum Simulation Hyperparameters (Qiskit Aer)", expanded=st.session_state.get("_quantum_expanded", False)):
    qc1, qc2, qc3, qc4 = st.columns(4)
    with qc1:
        qubits_val = st.selectbox("Active Qubits Budget", options=[4, 6, 8], index=[4, 6, 8].index(latest["selection"]["qubit_budget"]))
    with qc2:
        depth_val = st.slider("QAOA Depth (p layers)", min_value=1, max_value=3, value=st.session_state.pipeline.qaoa_depth)
    with qc3:
        shots_val = st.select_slider("Measurement Shots", options=[256, 512, 1024], value=st.session_state.pipeline.shots)
    with qc4:
        st.write("")
        st.write("")
        if st.button("🚀 Re-solve on Quantum Simulator", type="primary", use_container_width=True):
            st.session_state.pipeline.qubit_budget = qubits_val
            st.session_state.pipeline.qaoa_depth = depth_val
            st.session_state.pipeline.shots = shots_val
            cur_state = st.session_state.simulator.get_state()
            with st.spinner("Executing QAOA parameter optimization on quantum simulator..."):
                st.session_state.latest_result = st.session_state.pipeline.run(cur_state)
            msg = f"QAOA Quantum Optimization executed successfully! ({qubits_val} qubits, depth p={depth_val}, {shots_val} shots | Solved in {st.session_state.latest_result['execution_time_ms']:.1f} ms)."
            set_flash_message(msg, icon="⚛")
            st.session_state["_quantum_status"] = msg
            st.session_state["_quantum_expanded"] = True
            st.rerun()

    if "_quantum_status" in st.session_state:
        st.success(st.session_state["_quantum_status"], icon="✅")

st.markdown("---")

# Row 1: QUBO Heatmap & Mathematical Formulation
col_q1, col_q2 = st.columns([1.2, 1.0])

with col_q1:
    st.subheader("🔥 Dynamic QUBO Matrix Q (Traffic Delay + Constraints)")
    st.caption("Diagonal = Linear Traffic Delay Rewards | Off-diagonal = Adaptive Conflict Penalties & Arterial Synchronization")
    fig_heat = QuantumPlotVisualizer.plot_qubo_heatmap(qubo)
    st.plotly_chart(fig_heat, use_container_width=True)

with col_q2:
    st.subheader("📐 QUBO → Ising Hamiltonian Formulation")
    st.markdown("""
    Using the spin substitution $x_i = \\frac{\\mathbb{I} - Z_i}{2}$, the binary objective is converted into the cost Hamiltonian:
    """)
    st.latex(r"H_C = \sum_{i} h_i Z_i + \sum_{i < j} J_{ij} Z_i Z_j + C_{\text{offset}} \cdot \mathbb{I}")

    with st.expander("View Active Ising Pauli Coefficients", expanded=True):
        st.code(ising["ising_latex"][:300] + "...", language="text")
        st.write(f"**Total Qubits:** `{ising['num_qubits']}` | **Offset Energy:** `{ising['offset']:.2f}`")

    st.markdown("#### 🛡️ Adaptive Constraint Penalties")
    for pen in qubo.get("penalty_summary", []):
        st.markdown(
            f"- **Node {pen['intersection_id']}**: Priority `{pen['priority_score']:.2f}` $\\implies$ "
            f"Adaptive $\\lambda_i = {pen['adaptive_lambda']:.1f}$ (Quadratic coupling: `{pen['quadratic_term']:.1f}`)"
        )

st.markdown("---")

# Row 2: QAOA Circuit & Optimizer Convergence Trace
col_c1, col_c2 = st.columns([1.1, 1.3])

with col_c1:
    st.subheader("📉 QAOA Parameter Optimization (COBYLA)")
    st.caption(f"Optimal (γ, β) Angles: γ={qaoa['optimal_parameters']['gamma']}, β={qaoa['optimal_parameters']['beta']}")
    fig_conv = QuantumPlotVisualizer.plot_convergence_history(qaoa["convergence_history"])
    st.plotly_chart(fig_conv, use_container_width=True)

with col_c2:
    st.subheader("🔬 Parameterized QAOA Quantum Circuit Architecture")
    st.caption(f"Circuit Depth: {qaoa['circuit_depth']} | Gate Operations: {dict(qaoa['gate_counts'])}")

    circuit_str = QuantumPlotVisualizer.get_circuit_ascii(qaoa["optimal_circuit"])
    st.text_area("Qiskit Circuit ASCII Diagram", value=circuit_str, height=260)

st.markdown("---")

# Row 3: Measurement Sampling & Feasibility-Aware Decoding
st.subheader("🎲 Quantum Measurement Distribution & Feasibility-Aware Selection")
st.caption("Green = Selected Optimal Feasible | Cyan = Feasible Alternative | Red = Constraint Violation (Rejected)")

fig_dist = QuantumPlotVisualizer.plot_measurement_distribution(
    evaluated_solutions=dec["evaluated_solutions"],
    selected_bitstring=sol["bitstring"],
)
st.plotly_chart(fig_dist, use_container_width=True)

# Selected Configuration Summary Card
st.markdown("### 🏆 Feasibility-Aware Optimal Solution")
sc1, sc2, sc3, sc4 = st.columns(4)
with sc1:
    st.metric("Selected Bitstring |x⟩", sol["bitstring"], f"Prob: {sol['probability']*100:.1f}%")
with sc2:
    st.metric("Feasibility Status", "100% Valid Safe Plan" if sol["is_feasible"] else "Violations Repaired", "Zero Conflict")
with sc3:
    st.metric("QUBO Energy Cost", f"{sol['qubo_objective']:.2f}", f"Reduction: {sol['congestion_reduction_pct']}%")
with sc4:
    st.metric("Estimated Queue Clearance", f"-{sol['queue_reduction_veh']} veh", f"-{sol['wait_reduction_sec']:.1f}s delay")

st.markdown("#### 🚦 Resulting Deployed Signal Allocation:")
plan_cols = st.columns(len(latest["signal_plan"]))
for col, (node_id, timings) in zip(plan_cols, latest["signal_plan"].items()):
    with col:
        badge = "⚛ QAOA" if "AQSA" in timings.get("allocated_by", "") else "⚪ Heuristic"
        st.markdown(f"""
        <div style="background:#0f172a; border:1px solid #1e293b; border-radius:8px; padding:12px; text-align:center;">
            <div style="font-weight:700; color:#f8fafc; font-size:1.1rem;">Node {node_id}</div>
            <div style="font-size:0.75rem; color:#00f2fe; margin-bottom:8px;">{badge}</div>
            <div style="font-size:0.9rem; color:#cbd5e1;">Green N-S: <b style="color:#00e676;">{timings['green_ns']:.0f}s</b></div>
            <div style="font-size:0.9rem; color:#cbd5e1;">Green E-W: <b style="color:#38bdf8;">{timings['green_ew']:.0f}s</b></div>
        </div>
        """, unsafe_allow_html=True)
