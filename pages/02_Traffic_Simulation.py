"""
02_Traffic_Simulation.py: Detailed Traffic Simulator Sandbox.
Supports 4, 6, and 9 intersections, 6 predefined scenarios, discrete GPS vehicle kinematics,
real-time auto-tracking streaming, and queue progression dynamics.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.ui_common import apply_theme, render_brand_header, init_session_state, set_flash_message
from src.traffic.simulator import TrafficSimulator
from src.visualization.traffic_map import TrafficMapVisualizer

st.set_page_config(page_title="Simulation Sandbox | Q-TrafficAI", page_icon="🚗", layout="wide")
apply_theme()
init_session_state()

render_brand_header(subtitle="Urban Traffic Simulation Sandbox & Real-Time Fleet Generator")

sim = st.session_state.simulator

# Top Configuration Controls
st.subheader("⚙️ Simulation Environment Configuration")
c1, c2, c3, c4 = st.columns([1.2, 1.4, 1.2, 1.2])

with c1:
    grid_choice = st.selectbox(
        "Network Size (Intersections)",
        options=[4, 6, 9],
        index=[4, 6, 9].index(sim.num_intersections),
        help="4 (2x2 grid), 6 (2x3 grid), 9 (3x3 grid)",
    )

with c2:
    scenario_choice = st.selectbox(
        "Traffic Demand Scenario",
        options=list(TrafficSimulator.SCENARIOS.keys()),
        format_func=lambda s: f"{s.replace('_', ' ').title()} - {TrafficSimulator.SCENARIOS[s]['desc'][:35]}...",
        index=list(TrafficSimulator.SCENARIOS.keys()).index(sim.scenario),
    )

with c3:
    step_jump = st.number_input("Step Jump Count", min_value=1, max_value=30, value=5)

with c4:
    st.write("")
    st.write("")
    if st.button("Apply / Reset Grid", type="primary", width="stretch"):
        st.session_state.simulator = TrafficSimulator(num_intersections=grid_choice, scenario=scenario_choice, seed=42, city_name=sim.city_name)
        for _ in range(5):
            st.session_state.simulator.step()
        sim = st.session_state.simulator
        st.session_state.latest_result = st.session_state.pipeline.run(sim.get_state())
        msg = f"Initialized {grid_choice}-intersection network under '{scenario_choice.replace('_', ' ').title()}' successfully!"
        set_flash_message(msg, icon="🚦")
        st.session_state["_sim_status"] = msg
        st.rerun()

# Real-Time Controls Row
st.markdown("""
<div style="background:linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(13, 27, 42, 0.75) 100%); border:1px solid rgba(0, 242, 254, 0.25); border-radius:10px; padding:10px 16px; margin: 12px 0;">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="font-weight:700; color:#00f2fe; font-size:0.9rem;">📡 REAL-TIME SIMULATION & TELEMETRY STREAM</span>
        <span style="font-size:0.8rem; color:#94a3b8;">Continuous multi-modal vehicle kinematics and queue dynamics</span>
    </div>
</div>
""", unsafe_allow_html=True)

s1, s2, s3, s4, s5, s6 = st.columns([1.3, 1.1, 1.1, 1.2, 1.1, 1.0])
with s1:
    live_sim_toggle = st.toggle("🟢 Live Auto-Step", value=False, key="sim_live_toggle", help="Continuously step simulation in real-time")
with s2:
    sim_rate = st.selectbox("Interval", options=[1.0, 2.0, 3.0], format_func=lambda x: f"⚡ {x:.0f}s", index=1, key="sim_rate_sel")
with s3:
    if st.button("▶ Step (+2s)", width="stretch"):
        sim.step()
        set_flash_message(f"Simulated single step (+2.0s). Clock: {sim.time:.1f}s", icon="▶")
        st.rerun()
with s4:
    if st.button(f"⏩ Jump +{step_jump*2}s", width="stretch"):
        for _ in range(step_jump):
            sim.step()
        set_flash_message(f"Simulated {step_jump} steps forward (+{step_jump*2}s)", icon="⏩")
        st.rerun()
with s5:
    if st.button("🚨 Ambulance", width="stretch", type="secondary"):
        amb = sim.spawn_emergency_vehicle()
        set_flash_message(f"Emergency Ambulance {amb.id} dispatched into simulation!", icon="🚨")
        st.rerun()
with s6:
    if st.button("🔄 Reset", width="stretch"):
        sim.reset(scenario=scenario_choice)
        set_flash_message("Traffic simulation reset successfully.", icon="🔄")
        st.rerun()

st.markdown("---")

frag_sim_rate = sim_rate if live_sim_toggle else None

@st.fragment(run_every=frag_sim_rate)
def render_simulation_sandbox_fragment():
    sim_cur = st.session_state.simulator
    if live_sim_toggle:
        sim_cur.step()

    state = sim_cur.get_state()
    latest = st.session_state.latest_result
    selected_ids = latest["selection"]["selected_node_ids"]
    fleet_info = state.get("fleet_summary", {})

    # Two column layout: Live Map vs Time-series history
    col_map, col_ts = st.columns([1.2, 1.0])

    with col_map:
        st.subheader(f"🗺️ Live Network GPS State ({grid_choice} Intersections)")
        st.caption(
            "🟢 Green = Clear (<35%) | 🟡 Yellow = Medium (35-65%) | 🔴 Red = Heavy (>65%) | "
            f"🚗 {fleet_info.get('total_tracked', state['total_vehicles'])} Tracked Vehicles "
            f"({fleet_info.get('moving_count', 0)} Moving, {fleet_info.get('queued_count', state['total_queued'])} Queued)"
        )
        fig_net = TrafficMapVisualizer.create_network_figure(
            state,
            selected_nodes=selected_ids,
            map_style="open-street-map",
            city_name=sim_cur.city_name,
        )
        st.plotly_chart(fig_net, width="stretch", key=f"sim_map_{sim_cur.step_count}")

    with col_ts:
        st.subheader("📈 Real-Time Queue & Delay Dynamics")
        history = sim_cur.history
        if len(history) > 1:
            times = [h["timestamp"] for h in history]
            queues = [h["total_queued"] for h in history]
            waits = [h["global_avg_wait"] for h in history]

            fig_ts = go.Figure()
            fig_ts.add_trace(go.Scatter(x=times, y=queues, name="Total Queued (veh)", line=dict(color="#00f2fe", width=2.5)))
            fig_ts.add_trace(go.Scatter(x=times, y=waits, name="Avg Wait Time (s)", line=dict(color="#ffb300", width=2, dash="dot"), yaxis="y2"))

            fig_ts.update_layout(
                paper_bgcolor="#090d16",
                plot_bgcolor="#090d16",
                xaxis=dict(title="Simulation Time (s)", gridcolor="#1e293b", tickfont=dict(color="#94a3b8")),
                yaxis=dict(title="Queued Vehicles", gridcolor="#1e293b", tickfont=dict(color="#00f2fe")),
                yaxis2=dict(title="Avg Wait Time (s)", overlaying="y", side="right", tickfont=dict(color="#ffb300")),
                legend=dict(font=dict(color="#cbd5e1"), orientation="h", y=1.1, x=0.5, xanchor="center"),
                margin=dict(l=20, r=20, t=30, b=20),
                height=420,
            )
            st.plotly_chart(fig_ts, width="stretch", key=f"sim_ts_{sim_cur.step_count}")
        else:
            st.info("Advance simulation steps using the controls above to plot time-series telemetry.")

    st.markdown("---")

    # Intersections State Table
    st.subheader("📋 Detailed Intersections Telemetry")
    records = []
    for n_id, data in state["intersections"].items():
        records.append({
            "Intersection ID": n_id,
            "Total Vehicles": data["volume"],
            "Queued Vehicles": data["queue_length"],
            "Average Waiting Time": f"{data['avg_waiting_time']:.1f} s",
            "Road Occupancy": f"{data['occupancy']*100:.1f}%",
            "Density": f"{data['density']:.1f} veh/km",
            "Average Speed": f"{data['avg_speed']:.1f} m/s",
            "Congestion Index": f"{data['congestion_index']:.3f}",
            "Active Phase": data["current_phase"],
            "Green NS / EW": f"{data['green_ns']:.0f}s / {data['green_ew']:.0f}s",
        })

    st.dataframe(pd.DataFrame(records), width="stretch", hide_index=True)

render_simulation_sandbox_fragment()
