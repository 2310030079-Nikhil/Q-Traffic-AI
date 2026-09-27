"""
Q-TrafficAI: Adaptive Quantum Signal Allocation for AI-Driven Intelligent Traffic Optimization
Central Application Hub and Research Portal.
"""

import streamlit as st
import pandas as pd
from src.ui_common import apply_theme, render_brand_header, init_session_state, set_flash_message, render_architecture_flow

st.set_page_config(
    page_title="Q-TrafficAI | Quantum Traffic Intelligence",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()
init_session_state()

render_brand_header(subtitle="Final-Year CSE Major Project | AI + Quantum Optimization Research Platform")

# Top Highlights Row
col1, col2, col3, col4 = st.columns(4)

latest = st.session_state.latest_result
sim_state = st.session_state.simulator.get_state()

with col1:
    st.metric(
        label="🚗 Active Vehicles",
        value=sim_state["total_vehicles"],
        delta=f"{sim_state['total_queued']} queued",
        delta_color="inverse",
    )

with col2:
    st.metric(
        label="🚦 Signals Managed",
        value=sim_state["num_intersections"],
        delta=f"{len(latest['selection']['selected_node_ids'])} AQSA Critical",
    )

with col3:
    st.metric(
        label="⚛ Qubits Allocated",
        value=latest["selection"]["num_qubits"],
        delta=f"Depth p={latest['qaoa']['circuit_depth']}",
    )

with col4:
    st.metric(
        label="⚡ Optimization Speed",
        value=f"{latest['execution_time_ms']:.1f} ms",
        delta="100% Feasible Solution",
    )

st.markdown("---")

# Main Content Layout
left_col, right_col = st.columns([1.6, 1.0])

with left_col:
    st.subheader("🎯 Research Positioning & Core Contribution")
    st.markdown("""
    In smart city traffic management, quantum optimization using the **Quantum Approximate Optimization Algorithm (QAOA)**
    is often constrained by the NISQ qubit bottleneck and exponential state space explosion ($2^N$). Sending an entire
    urban grid indiscriminately into a quantum solver leads to barren plateaus, heavy circuit decoherence, and unfeasible solutions.

    **Q-TrafficAI introduces AQSA (Adaptive Quantum Signal Allocation):**
    > *Instead of sending the entire traffic network blindly into QAOA, AQSA intelligently identifies the most critical
    traffic-signal bottlenecks using AI-predicted conditions and uncertainty bounds, dynamically constructing a compact,
    coordination-aware quantum optimization problem.*
    """)

    st.markdown("#### 🔬 Distinct Methodological Separation")
    comp_df = pd.DataFrame([
        {"Component": "Traffic Prediction", "Technology": "AI (Random Forest + Uncertainty)", "Role": "Baseline Intelligence"},
        {"Component": "Signal Prioritization", "Technology": "AQSA Adaptive Scoring", "Role": "★ Proposed Novelty"},
        {"Component": "Qubit Variable Mapping", "Technology": "AQSA Priority Cutoff", "Role": "★ Proposed Novelty"},
        {"Component": "Dynamic QUBO Weights", "Technology": "AQSA Arterial Coordination", "Role": "★ Proposed Novelty"},
        {"Component": "Constraint Penalty Adaptation", "Technology": "AQSA Adaptive Penalties", "Role": "★ Proposed Novelty"},
        {"Component": "Quantum Circuit Execution", "Technology": "QAOA (Qiskit + Aer)", "Role": "Established Quantum Solver"},
        {"Component": "Feasibility Decoding", "Technology": "Feasibility-Aware Selection", "Role": "★ Proposed Novelty"},
        {"Component": "Closed-Loop Feedback", "Technology": "Discrete-Time Simulator", "Role": "Simulation Testbed"},
    ])
    st.dataframe(comp_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("🔁 Closed-Loop AQSA Pipeline Architecture")
    st.caption("End-to-end integration: Classical Edge Sensors → AI Uncertainty Forecaster → AQSA Qubit Pruning → QAOA Quantum Optimization → Conflict-Free Actuation")
    render_architecture_flow()

with right_col:
    st.subheader("⚡ Live Control Center Snapshot")
    st.markdown(f"""
    <div class="glass-card">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px;">
            <h4 style="color:#00f2fe; margin:0; font-family:'Outfit', sans-serif;">Traffic State: {sim_state['scenario'].upper()}</h4>
            <span style="background:rgba(0, 242, 254, 0.15); color:#00f2fe; border:1px solid rgba(0, 242, 254, 0.35); font-size:0.75rem; font-weight:700; padding:2px 8px; border-radius:6px;">LIVE ACTIVE</span>
        </div>
        <p style="color:#94a3b8; font-size:0.88rem; margin-bottom:12px;">Simulation Clock: <b style="color:#f8fafc;">{sim_state['timestamp']:.1f}s</b> (Step #{sim_state['step']})</p>
        <div style="margin: 14px 0;">
            <div style="display:flex; justify-content:space-between; font-size:0.85rem; color:#cbd5e1; margin-bottom:4px;">
                <span>Global Congestion Index</span>
                <span style="color:#00f2fe; font-weight:700;">{sim_state['global_congestion']*100:.1f}%</span>
            </div>
            <div style="background:#1e293b; border-radius:6px; height:10px; overflow:hidden;">
                <div style="background:linear-gradient(90deg, #00f2fe, #38bdf8, #a855f7); width:{min(100, int(sim_state['global_congestion']*100))}%; height:10px; border-radius:6px; box-shadow:0 0 10px rgba(0, 242, 254, 0.5);"></div>
            </div>
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:14px; font-size:0.84rem;">
            <div style="background:rgba(15, 23, 42, 0.6); padding:8px 12px; border-radius:8px; border:1px solid rgba(56, 189, 248, 0.15);">
                <div style="color:#94a3b8; font-size:0.75rem;">Active Qubits</div>
                <div style="color:#00f2fe; font-weight:700; font-size:1.05rem;">{latest['selection']['num_qubits']} Qubits</div>
            </div>
            <div style="background:rgba(15, 23, 42, 0.6); padding:8px 12px; border-radius:8px; border:1px solid rgba(56, 189, 248, 0.15);">
                <div style="color:#94a3b8; font-size:0.75rem;">Selected Bottlenecks</div>
                <div style="color:#a855f7; font-weight:700; font-size:1.05rem;">{', '.join(latest['selection']['selected_node_ids'])}</div>
            </div>
        </div>
        <div style="margin-top:12px; background:rgba(15, 23, 42, 0.8); border:1px dashed #334155; border-radius:8px; padding:10px 14px;">
            <div style="color:#94a3b8; font-size:0.75rem;">Best Quantum Ground State Bitstring:</div>
            <div style="color:#00e676; font-family:'JetBrains Mono', monospace; font-size:1.05rem; font-weight:700; letter-spacing:1px; margin-top:2px;">
                |{latest['decoding']['selected_solution']['bitstring']}⟩
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("🧭 Platform Navigation")
    pages_guide = [
        ("01_Dashboard", "🖥️ Live City Control Center", "Interactive network map, signal indicators, KPIs"),
        ("02_Traffic_Simulation", "🚗 Traffic Simulation Sandbox", "Scenarios (peak hour, spike, uneven), step-by-step"),
        ("03_AI_Prediction", "📈 AI Prediction & Uncertainty", "Random Forest forecast curves, 95% CI bands, metrics"),
        ("04_AQSA_Analysis", "🔬 AQSA Priority Analysis", "Dynamic priority scoring table, radar charts, selection logic"),
        ("05_Quantum_Optimization", "⚛ Quantum Deck (QAOA)", "QUBO heatmap, Ising formula, circuit view, measurements"),
        ("06_Comparison", "📊 Multi-Algorithm Benchmark", "Fixed vs Greedy vs Brute-Force vs QAOA vs AQSA"),
        ("07_Experiments", "🧪 Experiment & Ablation Lab", "Ablation A-E studies, threshold sensitivity, CSV export"),
        ("08_Research_Methodology", "📄 Academic Paper & Formulations", "Formal literature review, pseudocode, mathematical proofs"),
    ]

    for filename, title, desc in pages_guide:
        with st.expander(f"{title}"):
            st.write(desc)
            st.caption(f"Navigate using the sidebar to `pages/{filename}.py`")

    st.markdown("---")
    if st.button("🚀 Run One-Click AQSA Closed-Loop Cycle", use_container_width=True, type="primary"):
        # Advance simulator and re-run AQSA
        new_state = st.session_state.simulator.step(st.session_state.latest_result["signal_plan"])
        st.session_state.latest_result = st.session_state.pipeline.run(new_state)
        msg = f"Closed-loop AQSA cycle executed successfully! Signal plan updated for Step #{new_state['step']} ({new_state['timestamp']:.1f}s)."
        set_flash_message(msg, icon="🚀")
        st.session_state["_last_app_action"] = msg
        st.rerun()

    if "_last_app_action" in st.session_state:
        st.success(st.session_state["_last_app_action"], icon="✅")

st.markdown("---")
st.caption("Q-TrafficAI Platform | Department of Computer Science & Engineering | Major Project Research System")
