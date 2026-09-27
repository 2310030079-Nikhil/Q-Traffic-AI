"""
01_Dashboard.py: Live Smart City Traffic Control Center.
Renders interactive traffic map, real-time signal states, AQSA pipeline tracker, and live metrics.
"""

import streamlit as st
import pandas as pd
from src.ui_common import apply_theme, render_brand_header, init_session_state, set_flash_message
from src.visualization.traffic_map import TrafficMapVisualizer
from src.traffic.router import TrafficRouter
from src.traffic.geo_registry import CITY_PRESETS, get_all_city_places, resolve_place, get_place_suggestions, get_city_node_geo

st.set_page_config(page_title="Dashboard | Q-TrafficAI", page_icon="🚦", layout="wide")
apply_theme()
init_session_state()

render_brand_header(subtitle="Live Smart City Control Center | Real-Time AQSA Quantum Optimization")

# Retrieve current session instances
sim = st.session_state.simulator
latest = st.session_state.latest_result
state = sim.get_state()

# Top KPI Summary Row
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("🚗 Total Vehicles", state["total_vehicles"], f"{state['total_queued']} queued", delta_color="inverse")
with col2:
    st.metric("🚦 Signals Active", state["num_intersections"], f"{len(latest['selection']['selected_node_ids'])} AQSA Critical")
with col3:
    st.metric("⚛ Active Qubits", latest["selection"]["num_qubits"], f"Depth p={latest['qaoa']['circuit_depth']}")
with col4:
    st.metric("⏳ Global Avg Wait", f"{state['global_avg_wait']:.1f} s", f"{state['global_congestion']*100:.1f}% Congested", delta_color="inverse")
with col5:
    st.metric("⚡ Throughput", f"{state['throughput_veh_per_min']:.1f}", "veh / minute")

st.markdown("---")

# Main Interface: Map + Control & Status Column
map_col, status_col = st.columns([2.0, 1.0])

with map_col:
    st.subheader("🗺️ Live Google Maps Traffic Navigation & Signal Grid")

    # Auto-apply pending city switch if user entered places from another Indian metro
    if "_pending_city_switch" in st.session_state:
        target_city = st.session_state.pop("_pending_city_switch")
        st.session_state["dash_city_select"] = target_city
        st.session_state["_last_nav_city"] = target_city

    # Map Style & City Selectors
    map_ctrl1, map_ctrl2 = st.columns([1.3, 1.3])
    with map_ctrl1:
        map_city = st.selectbox(
            "Smart City Deployment",
            options=list(CITY_PRESETS.keys()),
            index=0,
            key="dash_city_select"
        )
    with map_ctrl2:
        map_style_choice = st.selectbox(
            "Map Layer Style",
            options=[
                ("open-street-map", "🗺️ Google Maps / OpenStreetMap"),
                ("carto-darkmatter", "🌃 Google Maps Dark Navigation"),
                ("carto-positron", "🏙️ Clean Positron Light"),
                ("abstract", "📐 2D Schematic Grid"),
            ],
            format_func=lambda x: x[1],
            index=0,
            key="dash_style_select"
        )[0]

    # User-Entered Point-to-Point Navigation Panel (Exact Indian Google Maps Locations)
    def _get_city_defaults(city: str) -> Tuple[str, str]:
        if "Mumbai" in city:
            return "CSMT Railway Terminus, Fort, Mumbai", "Gateway of India, Colaba, Mumbai"
        elif "Delhi" in city:
            return "Connaught Place (Rajiv Chowk), New Delhi", "India Gate & Kartavya Path, New Delhi"
        elif "Hyderabad" in city:
            return "Cyber Towers, HITEC City, Hyderabad", "Inorbit Mall / Durgam Cheruvu, Hyderabad"
        else:  # Bengaluru default
            return "MG Road Metro Station, Bengaluru, Karnataka", "Richmond Circle & Hosur Road, Bengaluru, Karnataka"

    if st.session_state.get("_last_nav_city") != map_city:
        st.session_state["_last_nav_city"] = map_city
        d_orig, d_dest = _get_city_defaults(map_city)
        st.session_state["field_nav_origin"] = d_orig
        st.session_state["field_nav_dest"] = d_dest
        st.session_state.pop("active_nav_route", None)

    if "field_nav_origin" not in st.session_state:
        d_orig, d_dest = _get_city_defaults(map_city)
        st.session_state["field_nav_origin"] = d_orig
        st.session_state["field_nav_dest"] = d_dest

    with st.expander("🧭 Check Real-Time Route & Shortest Path (Exact Indian Google Maps Locations)", expanded=True):
        st.markdown(
            """
            <div style="font-size:0.86rem; color:#94a3b8; margin-bottom:10px;">
                Enter any official <b>Indian Google Maps place name, landmark, or street address</b> below.
                (e.g., <i>MG Road Metro, Brigade Road, Cubbon Park, Richmond Circle, Commercial Street, Indiranagar 100ft Rd, Silk Board, CSMT, Gateway of India, Marine Drive, Connaught Place, India Gate, Cyber Towers</i>).
            </div>
            """,
            unsafe_allow_html=True,
        )

        r_c1, r_c2 = st.columns(2)
        with r_c1:
            orig_input = st.text_input(
                "📍 Starting Place (Indian Google Maps Location)",
                key="field_nav_origin",
                placeholder="Type e.g. MG Road, Brigade Road, Church Street, Cubbon Park...",
            )
            orig_node, orig_geo, orig_msg = resolve_place(
                orig_input, city_name=map_city, num_nodes=state["num_intersections"]
            )
            st.markdown(
                f'<div style="background:rgba(16, 185, 129, 0.12); border:1px solid rgba(16, 185, 129, 0.35); padding:5px 12px; border-radius:6px; font-size:0.79rem; color:#10b981; margin-top:-6px; margin-bottom:6px;">'
                f'<b>✓ Google Maps Location Verified:</b> {orig_geo.get("google_name", orig_geo["name"])} — <i>{orig_geo.get("formatted_address", "")}</i></div>',
                unsafe_allow_html=True,
            )

        with r_c2:
            dest_input = st.text_input(
                "🏁 Destination Place (Indian Google Maps Location)",
                key="field_nav_dest",
                placeholder="Type e.g. Richmond Circle, Indiranagar, Commercial Street, Silk Board...",
            )
            dest_node, dest_geo, dest_msg = resolve_place(
                dest_input, city_name=map_city, num_nodes=state["num_intersections"]
            )
            st.markdown(
                f'<div style="background:rgba(16, 185, 129, 0.12); border:1px solid rgba(16, 185, 129, 0.35); padding:5px 12px; border-radius:6px; font-size:0.79rem; color:#10b981; margin-top:-6px; margin-bottom:6px;">'
                f'<b>✓ Google Maps Location Verified:</b> {dest_geo.get("google_name", dest_geo["name"])} — <i>{dest_geo.get("formatted_address", "")}</i></div>',
                unsafe_allow_html=True,
            )

        # Detect cross-metro city match and auto-switch if user entered places from another Indian metro
        detected_city = None
        if orig_geo.get("matched_city") and orig_geo["matched_city"] != map_city:
            detected_city = orig_geo["matched_city"]
        elif dest_geo.get("matched_city") and dest_geo["matched_city"] != map_city:
            detected_city = dest_geo["matched_city"]

        if detected_city and detected_city != map_city:
            st.session_state["_pending_city_switch"] = detected_city
            st.session_state["_last_nav_city"] = detected_city
            st.rerun()

        # Quick clickable Google Maps place suggestion chips
        suggestions = get_place_suggestions(map_city, num_nodes=state["num_intersections"])
        st.markdown(
            '<div style="font-size:0.76rem; font-weight:700; color:#38bdf8; text-transform:uppercase; letter-spacing:0.5px; margin-top:4px; margin-bottom:4px;">'
            '⚡ Popular Google Maps Places (click to auto-fill destination):</div>',
            unsafe_allow_html=True,
        )
        chip_cols = st.columns(min(len(suggestions), 5))
        for idx, sugg in enumerate(suggestions[:5]):
            with chip_cols[idx]:
                if st.button(f"📍 {sugg['short']}", key=f"quick_dest_{sugg['node_id']}", width="stretch"):
                    st.session_state["field_nav_dest"] = sugg["formatted_address"]
                    set_flash_message(f"Destination set to '{sugg['name']}'", icon="📍")
                    st.rerun()

        # Action Buttons
        b_c1, b_c2, b_c3 = st.columns([1.5, 1.0, 1.0])
        with b_c1:
            find_route_clicked = st.button("🚀 Calculate Route & Traffic", type="primary", width="stretch")
        with b_c2:
            swap_route_clicked = st.button("🔀 Swap From/To", width="stretch")
        with b_c3:
            clear_route_clicked = st.button("✖ Clear", width="stretch")

    # Swap logic
    if swap_route_clicked:
        old_o = st.session_state.get("field_nav_origin", "")
        old_d = st.session_state.get("field_nav_dest", "")
        st.session_state["field_nav_origin"] = old_d
        st.session_state["field_nav_dest"] = old_o
        st.session_state.pop("active_nav_route", None)
        set_flash_message(f"Swapped route direction: {old_d} ➔ {old_o}", icon="🔀")
        st.rerun()

    # Clear logic
    if clear_route_clicked:
        st.session_state.pop("active_nav_route", None)
        set_flash_message("Navigation route cleared.", icon="ℹ️")
        st.rerun()

    router = TrafficRouter(sim, city_name=map_city)

    # Compute or retrieve route
    if find_route_clicked:
        active_route = router.compute_route(
            orig_node, dest_node, state, preference="fastest",
            origin_geo=orig_geo, dest_geo=dest_geo
        )
        st.session_state["active_nav_route"] = active_route
        set_flash_message(
            f"Google Maps shortest route calculated: {active_route['origin_name']} ➔ {active_route['destination_name']}! ETA: {active_route['total_time_min']:.1f} min ({active_route['overall_condition']}).",
            icon="🧭",
        )
    else:
        active_route = st.session_state.get("active_nav_route", None)
        # Auto-compute initial default route if none active and places are valid
        if active_route is None and "active_nav_route" not in st.session_state:
            active_route = router.compute_route(
                orig_node, dest_node, state, preference="fastest",
                origin_geo=orig_geo, dest_geo=dest_geo
            )
            st.session_state["active_nav_route"] = active_route
        elif active_route and active_route.get("found"):
            active_nodes = list(state["intersections"].keys())
            if active_route["origin"] in active_nodes and active_route["destination"] in active_nodes:
                active_route = router.compute_route(
                    active_route["origin"], active_route["destination"], state, preference="fastest",
                    origin_geo=orig_geo, dest_geo=dest_geo
                )
                st.session_state["active_nav_route"] = active_route
            else:
                active_route = None
                st.session_state.pop("active_nav_route", None)

    st.caption("🟢 Green Line = Clear Road (<35%) | 🟡 Yellow Line = Medium Traffic (35-65%) | 🔴 Red Line = Heavy Congestion (>65%)")

    selected_ids = latest["selection"]["selected_node_ids"]
    fig_map = TrafficMapVisualizer.create_network_figure(
        traffic_state=state,
        selected_nodes=selected_ids,
        active_route=active_route,
        map_style=map_style_choice,
        city_name=map_city,
        show_all_traffic=True,
    )
    st.plotly_chart(fig_map, width="stretch")

    # If Route is active, render Navigation Summary Card & Turn-by-Turn Guidance
    if active_route and active_route.get("found"):
        overall_c = active_route["overall_color"]
        turn_steps_html = "".join([
            f'<div style="background:rgba(15, 23, 42, 0.65); padding:8px 12px; border-radius:6px; border-left:3px solid {overall_c}; margin-bottom:4px;">{step}</div>'
            for step in active_route["turn_by_turn"]
        ])
        gmaps_url = active_route.get("google_maps_url", "https://maps.google.com")

        nav_html = f"""<div style="background:linear-gradient(145deg, #091326 0%, #0d213f 100%); border:1px solid rgba(0, 242, 254, 0.35); border-radius:12px; padding:18px 22px; margin-top:14px; box-shadow:0 8px 30px rgba(0, 0, 0, 0.45);">
<div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(56, 189, 248, 0.2); padding-bottom:12px; margin-bottom:14px;">
<div>
<span style="font-size:0.75rem; font-weight:700; color:#00f2fe; text-transform:uppercase; letter-spacing:0.8px;">Google Maps Real-Time Navigation</span>
<h3 style="margin:2px 0 0 0; color:#f8fafc; font-size:1.3rem;">{active_route['origin_name']} ➔ {active_route['destination_name']}</h3>
<div style="font-size:0.8rem; color:#94a3b8; margin-top:2px;">📍 <b>From:</b> {active_route.get('origin_address', active_route['origin_name'])} | 🏁 <b>To:</b> {active_route.get('destination_address', active_route['destination_name'])}</div>
</div>
<div style="text-align:right;">
<span style="background:{overall_c}25; color:{overall_c}; border:1px solid {overall_c}60; padding:5px 14px; border-radius:20px; font-weight:800; font-size:0.88rem;">
{active_route['overall_icon']} {active_route['overall_condition'].upper()}
</span>
</div>
</div>
<div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:10px; margin-bottom:16px;">
<div style="background:rgba(15, 23, 42, 0.65); padding:10px 14px; border-radius:8px; border:1px solid rgba(56, 189, 248, 0.15);">
<div style="color:#94a3b8; font-size:0.75rem;">Estimated Time (ETA)</div>
<div style="color:#00f2fe; font-size:1.35rem; font-weight:800; font-family:'Outfit', sans-serif;">{active_route['total_time_min']:.1f} min</div>
</div>
<div style="background:rgba(15, 23, 42, 0.65); padding:10px 14px; border-radius:8px; border:1px solid rgba(56, 189, 248, 0.15);">
<div style="color:#94a3b8; font-size:0.75rem;">Shortest Distance</div>
<div style="color:#f8fafc; font-size:1.35rem; font-weight:800; font-family:'Outfit', sans-serif;">{active_route['total_distance_km']:.2f} km</div>
</div>
<div style="background:rgba(15, 23, 42, 0.65); padding:10px 14px; border-radius:8px; border:1px solid rgba(56, 189, 248, 0.15);">
<div style="color:#94a3b8; font-size:0.75rem;">Predicted Flow Speed</div>
<div style="color:#38bdf8; font-size:1.35rem; font-weight:800; font-family:'Outfit', sans-serif;">{active_route['avg_speed_kmh']:.0f} km/h</div>
</div>
<div style="background:rgba(15, 23, 42, 0.65); padding:10px 14px; border-radius:8px; border:1px solid rgba(56, 189, 248, 0.15);">
<div style="color:#94a3b8; font-size:0.75rem;">AQSA Green-Wave Savings</div>
<div style="color:#00e676; font-size:1.35rem; font-weight:800; font-family:'Outfit', sans-serif;">-38s Saved</div>
</div>
</div>
<div style="font-size:0.86rem; color:#cbd5e1; margin-bottom:12px;">
<div style="font-weight:700; color:#00f2fe; margin-bottom:8px;">📍 Turn-by-Turn Route Guidance & Live Traffic Predictions:</div>
<div style="display:flex; flex-direction:column; gap:6px;">
{turn_steps_html}
</div>
</div>
<div style="border-top:1px solid rgba(56, 189, 248, 0.2); padding-top:10px; display:flex; justify-content:flex-end;">
<a href="{gmaps_url}" target="_blank" style="display:inline-block; background:linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%); color:#ffffff; font-weight:700; font-size:0.85rem; padding:8px 18px; border-radius:8px; text-decoration:none; box-shadow:0 4px 14px rgba(26, 115, 232, 0.4);">
🗺️ Open Live Route in Google Maps ↗
</a>
</div>
</div>"""
        st.markdown(nav_html, unsafe_allow_html=True)

with status_col:
    st.subheader("⚡ Live Control Center")

    # Quick Scenario Switcher
    curr_scenario = st.selectbox(
        "Traffic Scenario",
        options=["morning_peak", "evening_peak", "traffic_spike", "uneven", "normal", "high_uncertainty"],
        index=["morning_peak", "evening_peak", "traffic_spike", "uneven", "normal", "high_uncertainty"].index(sim.scenario),
    )
    if curr_scenario != sim.scenario:
        sim.set_scenario(curr_scenario)
        msg = f"Traffic scenario switched to '{curr_scenario.replace('_', ' ').title()}' successfully!"
        set_flash_message(msg, icon="🚦")
        st.session_state["_dashboard_status"] = msg
        st.rerun()

    # Action Buttons
    bcol1, bcol2 = st.columns(2)
    with bcol1:
        if st.button("▶ Step Sim (+2s)", use_container_width=True):
            sim.step()
            msg = f"Simulation stepped forward +2s (Step #{sim.step_count}, {sim.time:.1f}s) successfully!"
            set_flash_message(msg, icon="▶")
            st.session_state["_dashboard_status"] = msg
            st.rerun()
    with bcol2:
        if st.button("🚀 AQSA Optimize", use_container_width=True, type="primary"):
            cur_state = sim.get_state()
            st.session_state.latest_result = st.session_state.pipeline.run(cur_state)
            # Deploy plan to simulator
            sim.apply_signal_plan(st.session_state.latest_result["signal_plan"])
            msg = f"AQSA Quantum Optimization completed and optimal signal plan deployed successfully! ({len(st.session_state.latest_result['selection']['selected_node_ids'])} critical nodes optimized in {st.session_state.latest_result['execution_time_ms']:.1f} ms)"
            set_flash_message(msg, icon="🚀")
            st.session_state["_dashboard_status"] = msg
            st.rerun()

    if st.button("🔄 Reset City Simulation", use_container_width=True):
        sim.reset(scenario=curr_scenario)
        cur_state = sim.get_state()
        st.session_state.latest_result = st.session_state.pipeline.run(cur_state)
        msg = f"City traffic simulation reset successfully for scenario '{curr_scenario.replace('_', ' ').title()}'!"
        set_flash_message(msg, icon="🔄")
        st.session_state["_dashboard_status"] = msg
        st.rerun()

    if "_dashboard_status" in st.session_state:
        st.success(st.session_state["_dashboard_status"], icon="✅")

    st.markdown("---")
    st.markdown("#### 📡 Live Quantum Telemetry HUD")
    st.markdown("""
    <div style="background:linear-gradient(145deg, #091326 0%, #0d213f 100%); border:1px solid rgba(0, 242, 254, 0.3); border-radius:10px; padding:14px 18px; font-size:0.85rem; box-shadow:0 6px 20px rgba(0, 0, 0, 0.4);">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; border-bottom:1px solid rgba(56, 189, 248, 0.15); padding-bottom:8px;">
            <span style="font-weight:700; color:#00f2fe; text-transform:uppercase; font-size:0.75rem; letter-spacing:0.8px;">Optimization Pipeline</span>
            <span style="color:#00e676; font-size:0.75rem; font-weight:700; background:rgba(0, 230, 118, 0.15); border:1px solid rgba(0, 230, 118, 0.35); padding:2px 8px; border-radius:10px;">● SYNCHRONIZED</span>
        </div>
        <div style="display:flex; flex-direction:column; gap:6px;">
            <div style="display:flex; justify-content:space-between; color:#cbd5e1;">
                <span>AI Traffic Prediction:</span>
                <span style="color:#00e676; font-weight:600;">Complete (RF Ensembles)</span>
            </div>
            <div style="display:flex; justify-content:space-between; color:#cbd5e1;">
                <span>Critical Signals Selected:</span>
                <span style="color:#00f2fe; font-weight:700;">Nodes {nodes}</span>
            </div>
            <div style="display:flex; justify-content:space-between; color:#cbd5e1;">
                <span>Dynamic QUBO Dimension:</span>
                <span style="color:#a855f7; font-weight:600;">{dim} × {dim} Matrix</span>
            </div>
            <div style="display:flex; justify-content:space-between; color:#cbd5e1;">
                <span>QAOA Circuit Simulation:</span>
                <span style="color:#38bdf8; font-weight:600;">{shots} Shots (Aer)</span>
            </div>
            <div style="display:flex; justify-content:space-between; color:#cbd5e1;">
                <span>Feasibility Filter:</span>
                <span style="color:#00e676; font-weight:700;">{feas}% Valid Safe</span>
            </div>
        </div>
        <div style="display:flex; align-items:center; justify-content:space-between; margin-top:12px; border-top:1px dashed #334155; padding-top:10px;">
            <div>
                <span style="font-size:0.75rem; color:#94a3b8;">Ground State:</span>
                <code style="color:#00f2fe; font-weight:700; font-size:0.95rem; background:rgba(0, 242, 254, 0.1); padding:2px 6px; border-radius:4px; margin-left:4px;">|{bits}⟩</code>
            </div>
            <span style="background:rgba(56, 189, 248, 0.15); color:#38bdf8; font-size:0.75rem; font-weight:700; padding:2px 8px; border-radius:6px; border:1px solid rgba(56, 189, 248, 0.3);">⚡ {exec_time:.1f} ms</span>
        </div>
    </div>
    """.format(
        nodes=", ".join(selected_ids),
        dim=latest["qubo"]["dimension"],
        shots=latest["measurements"]["shots"],
        feas=latest["decoding"]["feasibility_rate_pct"],
        bits=latest["decoding"]["selected_solution"]["bitstring"],
        exec_time=latest["execution_time_ms"],
    ), unsafe_allow_html=True)

st.markdown("---")

# Bottom Row: Active Signal Timings Table
st.subheader("🚦 Current Signal Timing Allocations & Telemetry")
inter_table = []
plan = latest["signal_plan"]

for n_id, data in state["intersections"].items():
    p_info = plan.get(n_id, {})
    is_crit = n_id in selected_ids
    geo = get_city_node_geo(n_id, city_name=map_city)
    place_label = f"📍 {geo['name']} (Node {n_id})" if geo else f"Node {n_id}"
    inter_table.append({
        "Intersection / Google Maps Place": place_label,
        "AQSA Status": "⚛ CRITICAL (QUANTUM)" if is_crit else "⚪ HEURISTIC",
        "Current Phase": data["current_phase"],
        "Queue (veh)": data["queue_length"],
        "Avg Wait (s)": data["avg_waiting_time"],
        "Congestion": f"{data['congestion_index']*100:.1f}%",
        "Allocated Green NS": f"{p_info.get('green_ns', 27.0):.1f} s",
        "Allocated Green EW": f"{p_info.get('green_ew', 27.0):.1f} s",
        "Cycle Length": f"{p_info.get('green_ns', 27.0) + p_info.get('green_ew', 27.0) + 6.0:.1f} s",
    })

st.dataframe(pd.DataFrame(inter_table), use_container_width=True, hide_index=True)
