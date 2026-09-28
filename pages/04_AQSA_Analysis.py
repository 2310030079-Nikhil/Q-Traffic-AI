"""
04_AQSA_Analysis.py: Core Research Contribution Deep Dive.
Signal Priority Scoring, Dynamic Weight Adaptation, Adaptive Variable Selection,
and Threshold Sensitivity Analysis.
"""

import streamlit as st
import pandas as pd
import numpy as np
from src.ui_common import apply_theme, render_brand_header, init_session_state, set_flash_message
from src.visualization.charts import ChartVisualizer

st.set_page_config(page_title="AQSA Analysis | Q-TrafficAI", page_icon="🔬", layout="wide")
apply_theme()
init_session_state()

render_brand_header(subtitle="Stage 2 & 3: AQSA Signal Prioritization & Adaptive Quantum Variable Selection")

st.markdown("""
### 🧠 The Core Contribution: Adaptive Quantum Signal Allocation (AQSA)
Instead of naively encoding every intersection into a massive quantum circuit, **AQSA acts as an intelligent AI-quantum filter**.
It evaluates multi-dimensional traffic intelligence (Congestion, Queue Length, Wait Time, Density, and AI Uncertainty),
computes dynamic priority scores, and selects only the critical bottlenecks to map into quantum variables under a designated qubit budget.
""")

st.markdown("---")

latest = st.session_state.latest_result
priorities = latest["priorities"]
selection = latest["selection"]

raw_w = latest.get("adapted_weights", {})
if isinstance(raw_w, dict):
    adapted_w = raw_w
elif isinstance(raw_w, (list, tuple, np.ndarray)):
    adapted_w = {
        "w1_congestion": float(raw_w[0]),
        "w2_queue": float(raw_w[1]),
        "w3_wait_time": float(raw_w[2]),
        "w4_density": float(raw_w[3]),
        "w5_uncertainty": float(raw_w[4]),
    }
else:
    adapted_w = {
        "w1_congestion": 0.28,
        "w2_queue": 0.24,
        "w3_wait_time": 0.22,
        "w4_density": 0.14,
        "w5_uncertainty": 0.12,
    }

# Top Section: Priority Table & Factor Radar
col_table, col_radar = st.columns([1.4, 1.0])

with col_table:
    st.subheader("📋 AQSA Signal Priority Ranking Table")
    st.caption(f"Current Cutoff Threshold τ = {selection['threshold']:.2f} | Qubit Budget = {selection['qubit_budget']} qubits")

    sel_set = set(selection["selected_node_ids"])
    table_rows = []
    for n_id, p_info in sorted(priorities.items(), key=lambda x: x[1]["priority_score"], reverse=True):
        is_sel = n_id in sel_set
        table_rows.append({
            "Intersection": f"Node {n_id}",
            "Congestion (C_i)": f"{p_info['congestion_norm']:.3f}",
            "Queue (Q_i)": f"{p_info['raw_queue']} veh ({p_info['queue_norm']:.2f})",
            "Avg Wait (W_i)": f"{p_info['raw_wait']:.1f} s ({p_info['wait_norm']:.2f})",
            "Uncertainty (U_i)": f"±{p_info['raw_uncertainty_margin']:.1f} ({p_info['uncertainty_norm']:.3f})",
            "AQSA Priority Score": f"{p_info['priority_score']:.3f}",
            "Selected for Quantum": "✓ YES (QUANTUM)" if is_sel else "✗ NO (SKIPPED)",
        })

    st.dataframe(pd.DataFrame(table_rows), width="stretch", hide_index=True)

    # Search Space Reduction Badge
    red_pct = selection["reduction_ratio"] * 100.0
    st.markdown(f"""
    <div style="background:#0f172a; border:1px solid #1e293b; border-radius:8px; padding:10px 16px; margin-top:10px;">
        <span style="color:#00e676; font-weight:700;">Search Space Reduction:</span> 
        Selected <b>{len(selection['selected_nodes'])}</b> of <b>{len(priorities)}</b> intersections 
        ({red_pct:.1f}% reduction in quantum state dimensions).
    </div>
    """, unsafe_allow_html=True)

with col_radar:
    st.subheader("🎯 Priority Factor Radar Profile")
    fig_radar = ChartVisualizer.plot_priority_radar(priorities)
    st.plotly_chart(fig_radar, width="stretch")

st.markdown("---")

# Dynamic Weight Adaptation Explanation
st.subheader("⚖️ Dynamically Adapted Prioritization Weights")
st.markdown("""
$$\\text{Priority}_i = w_1(t) \\cdot \\tilde{C}_i + w_2(t) \\cdot \\tilde{Q}_i + w_3(t) \\cdot \\tilde{W}_i + w_4(t) \\cdot \\tilde{D}_i + w_5(t) \\cdot \\tilde{U}_i$$
AQSA dynamically shifts these weights based on real-time network variance, uncertainty spikes, and queue imbalances:
""")

w_cols = st.columns(5)
w_labels = [
    ("w1: Congestion", adapted_w["w1_congestion"], "Base 0.28"),
    ("w2: Queue Discrepancy", adapted_w["w2_queue"], "Base 0.24"),
    ("w3: Waiting Time", adapted_w["w3_wait_time"], "Base 0.22"),
    ("w4: Road Density", adapted_w["w4_density"], "Base 0.14"),
    ("w5: Prediction Uncertainty", adapted_w["w5_uncertainty"], "Base 0.12"),
]
for col, (name, val, base) in zip(w_cols, w_labels):
    with col:
        st.metric(name, f"{val:.3f}", base)

st.markdown("---")

# Selected Quantum Variables Breakdown
st.subheader("⚛ Selected Quantum Decision Variables & Phase Mapping")
st.caption("Only variables corresponding to high-priority bottlenecks enter the QUBO formulation")

var_meta = selection["variable_meta"]
var_rows = []
for v_name, meta in var_meta.items():
    var_rows.append({
        "Variable Name": f"`{v_name}`",
        "Intersection": f"Node {meta['intersection_id']}",
        "Phase Controlled": meta["phase"],
        "Physical Semantic Meaning": meta["description"],
    })

v_left, v_right = st.columns([1.4, 1.0])
with v_left:
    st.dataframe(pd.DataFrame(var_rows), width="stretch", hide_index=True)

with v_right:
    st.markdown("#### 🔍 Selection & Pruning Rationale")
    for s in selection["selected_nodes"]:
        st.markdown(f"🟢 **Node {s['intersection_id']}**: {s['reason']}")
    for s in selection["skipped_nodes"]:
        st.markdown(f"⚪ **Node {s['intersection_id']}**: {s['reason']}")

st.markdown("---")

# Threshold Sensitivity Analysis
st.subheader("📊 AQSA Priority Threshold Sensitivity Analysis (τ Sweep)")
st.markdown("Explore how adjusting the priority cutoff threshold $\\tau$ governs qubit demand and traffic objective efficiency:")

sweep_col1, sweep_col2 = st.columns([1.0, 1.8])

with sweep_col1:
    new_thresh = st.slider(
        "Interactive Selection Threshold (τ)",
        min_value=0.30,
        max_value=0.90,
        value=float(selection["threshold"]),
        step=0.05,
    )
    budget_options = [4, 6, 8]
    cur_budget = selection.get("qubit_budget", 6)
    budget_idx = budget_options.index(cur_budget) if cur_budget in budget_options else 1
    new_budget = st.selectbox("Quantum Qubit Budget (B)", options=budget_options, index=budget_idx)

    if st.button("Re-evaluate AQSA Selection", type="primary", width="stretch"):
        cur_state = st.session_state.simulator.get_state()
        st.session_state.latest_result = st.session_state.pipeline.run(
            traffic_state=cur_state,
            threshold=new_thresh,
            qubit_budget=new_budget,
        )
        msg = f"AQSA selection re-evaluated successfully! Cutoff τ = {new_thresh:.2f}, Qubit Budget = {new_budget} qubits ({len(st.session_state.latest_result['selection']['selected_node_ids'])} critical nodes selected)."
        set_flash_message(msg, icon="🔬")
        st.session_state["_aqsa_status"] = msg
        st.rerun()

    if "_aqsa_status" in st.session_state:
        st.success(st.session_state["_aqsa_status"], icon="✅")

with sweep_col2:
    exp_mgr = st.session_state.exp_manager
    sweep_df = exp_mgr.run_threshold_sweep(num_intersections=st.session_state.simulator.num_intersections)
    fig_sweep = ChartVisualizer.plot_threshold_sensitivity(sweep_df)
    st.plotly_chart(fig_sweep, width="stretch")
