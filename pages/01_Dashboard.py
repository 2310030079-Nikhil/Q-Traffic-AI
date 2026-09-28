"""
01_Dashboard.py: Live Smart City Traffic Control Center.
Renders real-time interactive traffic map, discrete GPS vehicle tracking,
real-world TomTom / OpenStreetMap live feeds, and real-time AQSA quantum optimization.
"""

from typing import Tuple, List, Dict, Any, Optional
import streamlit as st
import pandas as pd
from src.ui_common import apply_theme, render_brand_header, init_session_state, set_flash_message
from src.visualization.traffic_map import TrafficMapVisualizer
from src.traffic.router import TrafficRouter
from src.traffic.geo_registry import CITY_PRESETS, resolve_place, get_place_suggestions, get_city_node_geo
from src.traffic.live_api import LiveTrafficFeedManager

st.set_page_config(page_title="Live Dashboard | Q-TrafficAI", page_icon="🚦", layout="wide")
apply_theme()
init_session_state()

render_brand_header(subtitle="Live Smart City Control Center | Real-Time Multi-Modal GPS Tracking & AQSA Optimization")

sim = st.session_state.simulator
latest = st.session_state.latest_result

# Auto-apply pending city switch if user entered places from another Indian metro
if "_pending_city_switch" in st.session_state:
    target_city = st.session_state.pop("_pending_city_switch")
    st.session_state["dash_city_select"] = target_city
    st.session_state["_last_nav_city"] = target_city

# Top Control & Configuration Bar
top_c1, top_c2, top_c3 = st.columns([1.4, 1.2, 1.4])

with top_c1:
    map_city = st.selectbox(
        "🌆 Smart City Deployment",
        options=list(CITY_PRESETS.keys()),
        index=0,
        key="dash_city_select"
    )
    if sim.city_name != map_city:
        sim.set_city(map_city)

with top_c2:
    map_style_choice = st.selectbox(
        "🗺️ Map Layer Style",
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

with top_c3:
    curr_scenario = st.selectbox(
        "🚦 Traffic Scenario",
        options=["morning_peak", "evening_peak", "traffic_spike", "uneven", "normal", "high_uncertainty"],
        index=["morning_peak", "evening_peak", "traffic_spike", "uneven", "normal", "high_uncertainty"].index(sim.scenario),
        key="dash_scenario_select"
    )
    if curr_scenario != sim.scenario:
        sim.set_scenario(curr_scenario)
        set_flash_message(f"Traffic scenario switched to '{curr_scenario.replace('_', ' ').title()}'!", icon="🚦")
        st.rerun()

# Real-Time Live Tracking Control HUD
st.markdown("""
<div style="background:linear-gradient(135deg, rgba(15, 23, 42, 0.92) 0%, rgba(13, 27, 42, 0.85) 100%); border:1px solid rgba(0, 242, 254, 0.35); border-radius:12px; padding:12px 18px; margin-bottom:14px; box-shadow:0 6px 22px rgba(0, 0, 0, 0.45);">
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
        <div style="display:flex; align-items:center; gap:12px;">
            <span style="font-size:1.15rem; font-weight:800; color:#f8fafc; font-family:'Outfit', sans-serif;">📡 REAL-TIME TRAFFIC TRACKING</span>
            <span style="display:inline-flex; align-items:center; gap:6px; background:rgba(0, 230, 118, 0.15); border:1px solid rgba(0, 230, 118, 0.4); color:#00e676; font-size:0.75rem; font-weight:700; padding:3px 10px; border-radius:12px;">
                <span style="width:7px; height:7px; border-radius:50%; background:#00e676; box-shadow:0 0 10px #00e676;"></span> LIVE STREAM
            </span>
        </div>
        <div style="font-size:0.82rem; color:#94a3b8;">
            Discrete GPS Fleet Kinematics | Real-World Metro Corridors | Closed-Loop AQSA Sync
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4, ctrl_col5, ctrl_col6 = st.columns([1.3, 1.1, 1.3, 1.1, 1.2, 1.0])

with ctrl_col1:
    live_tracking = st.toggle("🟢 Live Auto-Tracking", value=True, key="live_tracking_toggle", help="Automatically advances simulation and vehicle GPS coordinates in real-time")

with ctrl_col2:
    refresh_rate = st.selectbox(
        "Refresh Rate",
        options=[1.0, 2.0, 3.0, 5.0],
        format_func=lambda x: f"⚡ {x:.0f}s ({'High' if x<=1 else ('Normal' if x<=2 else 'Relaxed')})",
        index=1,
        key="live_rate_select"
    )

with ctrl_col3:
    auto_aqsa = st.checkbox("⚛ Auto-AQSA Quantum", value=True, key="auto_aqsa_check", help="Periodically recalculates optimal signal timings with AQSA when traffic shifts")

with ctrl_col4:
    if st.button("▶ Step (+2s)", width="stretch", help="Advance simulation clock manually by 1 discrete step (+2.0s)"):
        sim.step()
        set_flash_message(f"Simulation advanced +2.0s (Step #{sim.step_count})", icon="▶")
        st.rerun()

with ctrl_col5:
    if st.button("🚨 Dispatch Ambulance", width="stretch", type="secondary", help="Inject priority emergency ambulance with active sirens and quantum green-wave preemption"):
        amb = sim.spawn_emergency_vehicle()
        set_flash_message(f"Priority Emergency Ambulance {amb.id} dispatched! Real-time green-wave preemption activated.", icon="🚨")
        st.rerun()

with ctrl_col6:
    if st.button("🔄 Reset Sim", width="stretch", help="Reset vehicle positions and simulation clock"):
        sim.reset(scenario=curr_scenario)
        st.session_state.latest_result = st.session_state.pipeline.run(sim.get_state())
        set_flash_message("Traffic simulation and fleet reset successfully.", icon="🔄")
        st.rerun()

# External Live Real-World Traffic Feeds Panel (TomTom / OSM)
with st.expander("🌐 External Real-World Live Traffic Feeds (TomTom & OpenStreetMap)", expanded=False):
    live_f_c1, live_f_c2 = st.columns([1.2, 1.8])
    with live_f_c1:
        st.markdown("##### 🔑 External Traffic API Key")
        tomtom_key = st.text_input(
            "TomTom API Key (Optional - Leave blank for Autonomous Real-Time Stream)",
            value=st.session_state.get("tomtom_api_key", ""),
            type="password",
            placeholder="Paste free TomTom API key...",
            help="Free key from developer.tomtom.com (2,500 free queries/day). When empty, Q-TrafficAI streams autonomous real-time telemetry."
        )
        if tomtom_key != st.session_state.get("tomtom_api_key", ""):
            st.session_state["tomtom_api_key"] = tomtom_key

        live_telemetry = LiveTrafficFeedManager.get_city_live_telemetry(map_city, api_key=tomtom_key)
        cond_col = live_telemetry["condition_color"]
        cond_ico = live_telemetry["condition_icon"]
        cong_p = live_telemetry["congestion_pct"]
        cond_lbl = live_telemetry["condition_label"]
        weather_cond = live_telemetry["weather"]["condition"]
        weather_temp = live_telemetry["weather"]["temperature_c"]
        feed_src = live_telemetry["source"]
        ist_clock = live_telemetry["timestamp_ist"]
        avg_spd = live_telemetry["avg_speed_kmh"]
        free_spd = live_telemetry["free_flow_speed_kmh"]

        st.markdown(
            f'<div style="background:rgba(15, 23, 42, 0.7); border:1px solid rgba(56, 189, 248, 0.25); border-radius:8px; padding:10px 14px; font-size:0.83rem;">'
            f'<div style="color:#00f2fe; font-weight:700; margin-bottom:4px;">📡 Active Feed: {feed_src}</div>'
            f'<div>⏱ <b>IST Clock:</b> {ist_clock}</div>'
            f'<div>🌦 <b>Weather:</b> {weather_cond} ({weather_temp}°C)</div>'
            f'<div>🚦 <b>City Congestion:</b> <span style="color:{cond_col}; font-weight:700;">{cond_ico} {cong_p}% ({cond_lbl})</span></div>'
            f'<div>⚡ <b>Avg Road Speed:</b> {avg_spd} km/h (Free Flow: {free_spd} km/h)</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        if st.button("🔄 Sync Simulation Demand to Live City Congestion", width="stretch"):
            if live_telemetry["congestion_index"] >= 0.65:
                sim.set_scenario("evening_peak" if "Evening" in live_telemetry.get("time_of_day_phase", "") else "morning_peak")
            elif live_telemetry["congestion_index"] >= 0.38:
                sim.set_scenario("normal")
            else:
                sim.set_scenario("uneven")
            set_flash_message(f"Simulation calibrated to match live {map_city} congestion ({live_telemetry['congestion_pct']}%)!", icon="🔄")
            st.rerun()

    with live_f_c2:
        st.markdown("##### 🛣️ Live Arterial Corridors & Real-Time Incident Advisory")
        corr_df = pd.DataFrame(live_telemetry["arterial_corridors"])[["corridor", "road_type", "current_speed_kmh", "congestion_pct", "delay_min", "status"]]
        corr_df.columns = ["Corridor / Landmark", "Type", "Speed (km/h)", "Congestion", "Delay", "Status"]
        st.dataframe(corr_df, width="stretch", hide_index=True)

        st.markdown("<b>⚠️ Active City Incidents:</b>", unsafe_allow_html=True)
        inc_cols = st.columns(len(live_telemetry["incidents"]))
        for idx, inc in enumerate(live_telemetry["incidents"]):
            with inc_cols[idx]:
                st.markdown(
                    f'<div style="background:rgba(15, 23, 42, 0.6); border-left:3px solid {"#ef4444" if inc["severity"]=="red" else "#f59e0b"}; border-radius:6px; padding:6px 10px; font-size:0.78rem;">'
                    f'<div style="font-weight:700; color:#f8fafc;">{inc["type"]}</div>'
                    f'<div style="color:#94a3b8;">📍 {inc["location"]}</div>'
                    f'<div style="color:#38bdf8;">{inc["impact"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

# Point-to-Point Navigation Panel (Exact Indian Google Maps Locations)
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

with st.expander("🧭 Live Route Navigation & Travel Time Calculator (Exact Indian Google Maps Locations)", expanded=True):
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
            orig_input, city_name=map_city, num_nodes=sim.num_intersections
        )
        st.markdown(
            f'<div style="background:rgba(16, 185, 129, 0.12); border:1px solid rgba(16, 185, 129, 0.35); padding:5px 12px; border-radius:6px; font-size:0.79rem; color:#10b981; margin-top:-6px; margin-bottom:6px;">'
            f'<b>✓ Location Verified:</b> {orig_geo.get("google_name", orig_geo["name"])} — <i>{orig_geo.get("formatted_address", "")}</i></div>',
            unsafe_allow_html=True,
        )

    with r_c2:
        dest_input = st.text_input(
            "🏁 Destination Place (Indian Google Maps Location)",
            key="field_nav_dest",
            placeholder="Type e.g. Richmond Circle, Indiranagar, Commercial Street, Silk Board...",
        )
        dest_node, dest_geo, dest_msg = resolve_place(
            dest_input, city_name=map_city, num_nodes=sim.num_intersections
        )
        st.markdown(
            f'<div style="background:rgba(16, 185, 129, 0.12); border:1px solid rgba(16, 185, 129, 0.35); padding:5px 12px; border-radius:6px; font-size:0.79rem; color:#10b981; margin-top:-6px; margin-bottom:6px;">'
            f'<b>✓ Location Verified:</b> {dest_geo.get("google_name", dest_geo["name"])} — <i>{dest_geo.get("formatted_address", "")}</i></div>',
            unsafe_allow_html=True,
        )

    # Detect cross-metro city match
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
    suggestions = get_place_suggestions(map_city, num_nodes=sim.num_intersections)
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

    b_c1, b_c2, b_c3 = st.columns([1.5, 1.0, 1.0])
    with b_c1:
        find_route_clicked = st.button("🚀 Calculate Route & Travel Time", type="primary", width="stretch")
    with b_c2:
        swap_route_clicked = st.button("🔀 Swap From/To", width="stretch")
    with b_c3:
        clear_route_clicked = st.button("✖ Clear", width="stretch")

    router = TrafficRouter(sim, city_name=map_city)

    if swap_route_clicked:
        old_o = st.session_state.get("field_nav_origin", "")
        old_d = st.session_state.get("field_nav_dest", "")
        st.session_state["field_nav_origin"] = old_d
        st.session_state["field_nav_dest"] = old_o
        st.session_state.pop("active_nav_route", None)
        set_flash_message(f"Swapped route direction: {old_d} ➔ {old_o}", icon="🔀")
        st.rerun()

    if clear_route_clicked:
        st.session_state.pop("active_nav_route", None)
        set_flash_message("Navigation route cleared.", icon="ℹ️")
        st.rerun()

    # Route Computation
    if find_route_clicked:
        active_route = router.compute_route(
            orig_node, dest_node, sim.get_state(), preference="fastest",
            origin_geo=orig_geo, dest_geo=dest_geo
        )
        st.session_state["active_nav_route"] = active_route
        set_flash_message(
            f"Route calculated: {active_route['origin_name']} ➔ {active_route['destination_name']}! Travel Time: {active_route['total_time_formatted']} ({active_route['overall_condition']}).",
            icon="🧭",
        )
    else:
        active_route = st.session_state.get("active_nav_route", None)
        if active_route is None and "active_nav_route" not in st.session_state:
            active_route = router.compute_route(
                orig_node, dest_node, sim.get_state(), preference="fastest",
                origin_geo=orig_geo, dest_geo=dest_geo
            )
            st.session_state["active_nav_route"] = active_route

    # Real-Time Journey Time & ETA Telemetry HUD Card
    if active_route and active_route.get("found"):
        overall_c = active_route["overall_color"]
        st.markdown(
            f"""<div style="background:linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(13, 33, 63, 0.95) 100%); border:1px solid rgba(0, 242, 254, 0.35); border-radius:12px; padding:16px 20px; margin-top:14px; margin-bottom:12px; box-shadow:0 8px 30px rgba(0, 0, 0, 0.45);">
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(56, 189, 248, 0.2); padding-bottom:10px; margin-bottom:12px;">
                    <div>
                        <span style="font-size:0.75rem; font-weight:700; color:#00f2fe; text-transform:uppercase; letter-spacing:0.8px;">⏱️ Journey Time & Real-Time ETA Telemetry</span>
                        <h4 style="margin:2px 0 0 0; color:#f8fafc; font-size:1.15rem;">{active_route['origin_name']} ➔ {active_route['destination_name']}</h4>
                    </div>
                    <div>
                        <span style="background:{overall_c}25; color:{overall_c}; border:1px solid {overall_c}60; padding:5px 14px; border-radius:20px; font-weight:800; font-size:0.82rem;">
                            {active_route['overall_icon']} {active_route['overall_condition'].upper()} TRAFFIC
                        </span>
                    </div>
                </div>
                <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap:10px; margin-bottom:8px;">
                    <div style="background:rgba(0, 242, 254, 0.08); border:1px solid rgba(0, 242, 254, 0.35); padding:10px 14px; border-radius:8px;">
                        <div style="color:#94a3b8; font-size:0.73rem; text-transform:uppercase; font-weight:600;">⏱️ How Long to Reach</div>
                        <div style="color:#00f2fe; font-size:1.45rem; font-weight:800; font-family:'Outfit', sans-serif;">{active_route['total_time_formatted']}</div>
                        <div style="color:#38bdf8; font-size:0.76rem;">Duration: {active_route['total_time_min']:.1f} min</div>
                    </div>
                    <div style="background:rgba(16, 185, 129, 0.08); border:1px solid rgba(16, 185, 129, 0.35); padding:10px 14px; border-radius:8px;">
                        <div style="color:#94a3b8; font-size:0.73rem; text-transform:uppercase; font-weight:600;">🏁 Expected Arrival (IST)</div>
                        <div style="color:#10b981; font-size:1.45rem; font-weight:800; font-family:'Outfit', sans-serif;">{active_route.get('arrival_time_ist', '--:--')}</div>
                        <div style="color:#6ee7b7; font-size:0.76rem;">Depart: {active_route.get('departure_time_ist', '--:--')}</div>
                    </div>
                    <div style="background:rgba(255, 255, 255, 0.04); border:1px solid rgba(255, 255, 255, 0.12); padding:10px 14px; border-radius:8px;">
                        <div style="color:#94a3b8; font-size:0.73rem; text-transform:uppercase; font-weight:600;">📏 Journey Distance</div>
                        <div style="color:#f8fafc; font-size:1.45rem; font-weight:800; font-family:'Outfit', sans-serif;">{active_route['total_distance_km']:.2f} km</div>
                        <div style="color:#cbd5e1; font-size:0.76rem;">Avg Speed: {active_route['avg_speed_kmh']:.0f} km/h</div>
                    </div>
                    <div style="background:rgba(245, 158, 11, 0.08); border:1px solid rgba(245, 158, 11, 0.3); padding:10px 14px; border-radius:8px;">
                        <div style="color:#94a3b8; font-size:0.73rem; text-transform:uppercase; font-weight:600;">🚦 Congestion Delay</div>
                        <div style="color:#f59e0b; font-size:1.45rem; font-weight:800; font-family:'Outfit', sans-serif;">+{active_route.get('delay_time_min', 0.0):.1f} min</div>
                        <div style="color:#34d399; font-size:0.76rem;">AQSA Savings: -{active_route.get('aqsa_savings_sec', 38):.0f}s green wave</div>
                    </div>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

        with st.expander(f"📊 Destination Travel Time Matrix: How long to reach other destinations from '{orig_geo.get('name', 'Starting Point')}'?", expanded=False):
            st.caption(f"Real-time travel times and estimated arrival times from **{orig_geo.get('name', 'Origin')}** to all key destinations across the city under current live traffic:")
            all_dest_etas = router.compute_all_destinations_eta(orig_node, sim.get_state(), origin_geo=orig_geo)
            if all_dest_etas:
                eta_table = []
                for d in all_dest_etas:
                    cond_icon = d.get("condition_icon", d.get("icon", "🟢"))
                    cond_name = d.get("condition", "CLEAR").upper()
                    eta_table.append({
                        "Destination Landmark": f"📍 {d.get('destination_name', 'Destination')}",
                        "Travel Time (How long to reach)": d.get("travel_time_formatted", f"{d.get('travel_time_min', 0):.1f} min"),
                        "Expected Arrival (IST)": d.get("arrival_time_ist", "--:--"),
                        "Distance": f"{d.get('distance_km', 0.0)} km",
                        "Traffic Status": f"{cond_icon} {cond_name}",
                        "Corridor Speed": f"{d.get('avg_speed_kmh', 35.0)} km/h",
                    })
                st.dataframe(pd.DataFrame(eta_table), width="stretch", hide_index=True)

st.markdown("---")

# REAL-TIME FRAGMENT CONTAINER
# Auto-refreshes when live tracking is active without reloading the whole page or interrupting inputs
fragment_rate = refresh_rate if live_tracking else None

@st.fragment(run_every=fragment_rate)
def render_live_traffic_grid():
    sim_inst = st.session_state.simulator
    pipe_inst = st.session_state.pipeline

    # If live tracking is active, step the discrete simulation forward
    if live_tracking:
        sim_inst.step()
        # Periodic or demand-driven AQSA quantum optimization pass
        if auto_aqsa and (sim_inst.step_count % 6 == 0 or sim_inst.emergency_preemption_active):
            fresh_state = sim_inst.get_state()
            st.session_state.latest_result = pipe_inst.run(fresh_state)
            sim_inst.apply_signal_plan(st.session_state.latest_result["signal_plan"])

    state_snap = sim_inst.get_state()
    res_snap = st.session_state.latest_result
    fleet_info = state_snap.get("fleet_summary", {})

    # Top KPI Summary Row
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.metric(
            "🚗 Active Fleet",
            f"{fleet_info.get('total_tracked', state_snap['total_vehicles'])} vehicles",
            f"{fleet_info.get('moving_count', 0)} moving | {fleet_info.get('queued_count', state_snap['total_queued'])} queued",
            delta_color="off"
        )
    with k2:
        amb_label = "🚨 EMERGENCY ACTIVE" if fleet_info.get("emergency_active") else "⚪ Normal Routine"
        st.metric(
            "🚦 Signals Active",
            f"{state_snap['num_intersections']} Junctions",
            amb_label,
            delta_color="normal" if not fleet_info.get("emergency_active") else "inverse"
        )
    with k3:
        st.metric(
            "⚛ Active Qubits",
            res_snap["selection"]["num_qubits"],
            f"Depth p={res_snap['qaoa']['circuit_depth']} (Aer)",
            delta_color="off"
        )
    with k4:
        st.metric(
            "⏳ Global Avg Wait",
            f"{state_snap['global_avg_wait']:.1f} s",
            f"{state_snap['global_congestion']*100:.1f}% Congested",
            delta_color="inverse"
        )
    with k5:
        st.metric(
            "⚡ Fleet Speed",
            f"{fleet_info.get('avg_speed_kmh', 38.0):.1f} km/h",
            f"Throughput {state_snap['throughput_veh_per_min']:.0f} veh/min",
            delta_color="normal"
        )

    # Interactive Traffic Map + Control Column
    map_col, status_col = st.columns([2.1, 1.0])

    with map_col:
        st.subheader("🗺️ Live Google Maps Traffic Navigation & GPS Vehicle Stream")
        st.caption(
            "🟢 Green = Clear (<35%) | 🟡 Yellow = Medium (35-65%) | 🔴 Red = Heavy (>65%) | "
            "🚗 Moving Vehicles | 🚌 City Buses | 🚨 Emergency Ambulances (Priority Green Wave)"
        )

        selected_ids = res_snap["selection"]["selected_node_ids"]
        cur_route = st.session_state.get("active_nav_route", None)

        fig_map = TrafficMapVisualizer.create_network_figure(
            traffic_state=state_snap,
            selected_nodes=selected_ids,
            active_route=cur_route,
            map_style=map_style_choice,
            city_name=map_city,
            show_all_traffic=True,
        )
        st.plotly_chart(fig_map, width="stretch", key=f"live_plotly_map_{sim_inst.step_count}")

        # Route Summary Card if active
        if cur_route and cur_route.get("found"):
            overall_c = cur_route["overall_color"]
            turn_steps_html = "".join([
                f'<div style="background:rgba(15, 23, 42, 0.65); padding:7px 12px; border-radius:6px; border-left:3px solid {overall_c}; margin-bottom:4px; font-size:0.84rem;">{step}</div>'
                for step in cur_route["turn_by_turn"]
            ])
            gmaps_url = cur_route.get("google_maps_url", "https://maps.google.com")

            nav_html = f"""<div style="background:linear-gradient(145deg, #091326 0%, #0d213f 100%); border:1px solid rgba(0, 242, 254, 0.35); border-radius:12px; padding:16px 20px; margin-top:12px; box-shadow:0 8px 30px rgba(0, 0, 0, 0.45);">
<div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(56, 189, 248, 0.2); padding-bottom:10px; margin-bottom:12px;">
<div>
<span style="font-size:0.74rem; font-weight:700; color:#00f2fe; text-transform:uppercase; letter-spacing:0.8px;">Google Maps Real-Time Navigation</span>
<h4 style="margin:2px 0 0 0; color:#f8fafc; font-size:1.15rem;">{cur_route['origin_name']} ➔ {cur_route['destination_name']}</h4>
</div>
<div>
<span style="background:{overall_c}25; color:{overall_c}; border:1px solid {overall_c}60; padding:4px 12px; border-radius:20px; font-weight:800; font-size:0.82rem;">
{cur_route['overall_icon']} {cur_route['overall_condition'].upper()}
</span>
</div>
</div>
<div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:8px; margin-bottom:12px;">
<div style="background:rgba(15, 23, 42, 0.65); padding:8px 12px; border-radius:8px; border:1px solid rgba(56, 189, 248, 0.15);">
<div style="color:#94a3b8; font-size:0.72rem;">Travel Time (ETA)</div>
<div style="color:#00f2fe; font-size:1.25rem; font-weight:800; font-family:'Outfit', sans-serif;">{cur_route.get('total_time_formatted', f"{cur_route['total_time_min']:.1f} min")}</div>
<div style="color:#38bdf8; font-size:0.74rem;">🏁 Arrival: {cur_route.get('arrival_time_ist', '--:--')}</div>
</div>
<div style="background:rgba(15, 23, 42, 0.65); padding:8px 12px; border-radius:8px; border:1px solid rgba(56, 189, 248, 0.15);">
<div style="color:#94a3b8; font-size:0.72rem;">Shortest Distance</div>
<div style="color:#f8fafc; font-size:1.25rem; font-weight:800; font-family:'Outfit', sans-serif;">{cur_route['total_distance_km']:.2f} km</div>
<div style="color:#94a3b8; font-size:0.74rem;">Avg Speed: {cur_route['avg_speed_kmh']:.0f} km/h</div>
</div>
<div style="background:rgba(15, 23, 42, 0.65); padding:8px 12px; border-radius:8px; border:1px solid rgba(56, 189, 248, 0.15);">
<div style="color:#94a3b8; font-size:0.72rem;">Traffic Delay</div>
<div style="color:#f59e0b; font-size:1.25rem; font-weight:800; font-family:'Outfit', sans-serif;">+{cur_route.get('delay_time_min', 0.0):.1f} min</div>
<div style="color:#94a3b8; font-size:0.74rem;">Free Flow: {cur_route.get('free_flow_time_min', cur_route['total_time_min']):.1f} min</div>
</div>
<div style="background:rgba(15, 23, 42, 0.65); padding:8px 12px; border-radius:8px; border:1px solid rgba(56, 189, 248, 0.15);">
<div style="color:#94a3b8; font-size:0.72rem;">AQSA Savings</div>
<div style="color:#00e676; font-size:1.25rem; font-weight:800; font-family:'Outfit', sans-serif;">-{cur_route.get('aqsa_savings_sec', 38):.0f}s Saved</div>
<div style="color:#00e676; font-size:0.74rem;">Quantum Green Wave</div>
</div>
</div>
<div style="border-top:1px solid rgba(56, 189, 248, 0.2); padding-top:8px; display:flex; justify-content:flex-end;">
<a href="{gmaps_url}" target="_blank" style="display:inline-block; background:linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%); color:#ffffff; font-weight:700; font-size:0.82rem; padding:6px 14px; border-radius:6px; text-decoration:none;">
🗺️ Open in Google Maps ↗
</a>
</div>
</div>"""
            st.markdown(nav_html, unsafe_allow_html=True)

    with status_col:
        st.subheader("⚡ Quantum Control Center")

        # Telemetry HUD Card
        st.markdown("""
        <div style="background:linear-gradient(145deg, #091326 0%, #0d213f 100%); border:1px solid rgba(0, 242, 254, 0.3); border-radius:10px; padding:14px 18px; font-size:0.85rem; box-shadow:0 6px 20px rgba(0, 0, 0, 0.4);">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; border-bottom:1px solid rgba(56, 189, 248, 0.15); padding-bottom:8px;">
                <span style="font-weight:700; color:#00f2fe; text-transform:uppercase; font-size:0.75rem; letter-spacing:0.8px;">Optimization Pipeline</span>
                <span style="color:#00e676; font-size:0.75rem; font-weight:700; background:rgba(0, 230, 118, 0.15); border:1px solid rgba(0, 230, 118, 0.35); padding:2px 8px; border-radius:10px;">● SYNCHRONIZED</span>
            </div>
            <div style="display:flex; flex-direction:column; gap:6px;">
                <div style="display:flex; justify-content:space-between; color:#cbd5e1;">
                    <span>Simulation Clock:</span>
                    <span style="color:#38bdf8; font-weight:700;">{sim_time:.1f}s (Step #{step})</span>
                </div>
                <div style="display:flex; justify-content:space-between; color:#cbd5e1;">
                    <span>Live Tracking Mode:</span>
                    <span style="color:#00e676; font-weight:600;">{mode}</span>
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
                    <span>Emergency Preemption:</span>
                    <span style="color:{amb_color}; font-weight:700;">{amb_text}</span>
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
            sim_time=state_snap["timestamp"],
            step=state_snap["step"],
            mode="Active Continuous (Auto)" if live_tracking else "Paused / Single-Step",
            nodes=", ".join(selected_ids),
            dim=res_snap["qubo"]["dimension"],
            shots=res_snap["measurements"]["shots"],
            amb_color="#ef4444" if fleet_info.get("emergency_active") else "#10b981",
            amb_text="🚨 ACTIVE (GREEN WAVE)" if fleet_info.get("emergency_active") else "STANDBY",
            bits=res_snap["decoding"]["selected_solution"]["bitstring"],
            exec_time=res_snap["execution_time_ms"],
        ), unsafe_allow_html=True)

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

        if st.button("🚀 Run AQSA Optimization Now", width="stretch", type="primary"):
            st.session_state.latest_result = pipe_inst.run(state_snap)
            sim_inst.apply_signal_plan(st.session_state.latest_result["signal_plan"])
            set_flash_message(f"Manual AQSA Quantum Optimization executed successfully! ({res_snap['execution_time_ms']:.1f} ms)", icon="🚀")
            st.rerun()

    # REAL-TIME FLEET TELEMETRY SECTION
    st.markdown("---")
    st.subheader("🛰️ Real-Time GPS Vehicle Fleet Telemetry Tracker")

    tracked_vehs = state_snap.get("tracked_vehicles", [])
    if tracked_vehs:
        fl_c1, fl_c2, fl_c3 = st.columns([1.2, 1.2, 1.6])
        with fl_c1:
            type_filter = st.selectbox(
                "Filter Vehicle Category",
                options=["All Vehicles", "🚨 Emergency Ambulances", "🚌 City Transit Buses", "🚗 Passenger Cars", "🚖 EV Taxis", "🛺 Auto Rickshaws"],
                index=0,
                key="fleet_type_filter"
            )
        with fl_c2:
            status_filter = st.selectbox(
                "Filter Queue Status",
                options=["All Statuses", "🟢 Moving Free-Flow", "🔴 Queued at Red Light"],
                index=0,
                key="fleet_status_filter"
            )
        with fl_c3:
            search_query = st.text_input("🔍 Search by Vehicle ID or Road Corridor", placeholder="e.g. AMB, BUS, CAR-104, MG Road...", key="fleet_search_input")

        # Apply filtering
        filtered_vehs = tracked_vehs
        if type_filter == "🚨 Emergency Ambulances":
            filtered_vehs = [v for v in filtered_vehs if v.get("is_emergency")]
        elif type_filter == "🚌 City Transit Buses":
            filtered_vehs = [v for v in filtered_vehs if v.get("type") == "Bus"]
        elif type_filter == "🚗 Passenger Cars":
            filtered_vehs = [v for v in filtered_vehs if v.get("type") == "Car"]
        elif type_filter == "🚖 EV Taxis":
            filtered_vehs = [v for v in filtered_vehs if v.get("type") == "EV Taxi"]
        elif type_filter == "🛺 Auto Rickshaws":
            filtered_vehs = [v for v in filtered_vehs if v.get("type") == "Auto Rickshaw"]

        if status_filter == "🟢 Moving Free-Flow":
            filtered_vehs = [v for v in filtered_vehs if not v.get("is_queued")]
        elif status_filter == "🔴 Queued at Red Light":
            filtered_vehs = [v for v in filtered_vehs if v.get("is_queued")]

        if search_query.strip():
            sq = search_query.strip().lower()
            filtered_vehs = [v for v in filtered_vehs if sq in v.get("id", "").lower() or sq in v.get("edge", "").lower()]

        # Format dataframe
        table_rows = []
        for v in filtered_vehs:
            table_rows.append({
                "Vehicle ID": f"{v.get('icon', '🚗')} {v.get('id')}",
                "Type": v.get("type"),
                "Speed": f"{v.get('speed_kmh', 0.0):.1f} km/h",
                "Road Corridor": v.get("edge"),
                "Progress": f"{v.get('progress_pct', 0)}%",
                "Est. Time to Dest": v.get("eta_destination", f"{v.get('eta_min', 1.0):.1f}m"),
                "Status": "🔴 Queued at Signal" if v.get("is_queued") else ("🚨 Emergency En Route" if v.get("is_emergency") else "🟢 Cruising"),
                "Wait Time": f"{v.get('waiting_time_s', 0.0):.1f} s",
                "Live GPS Coordinates": f"{v.get('lat', 0.0):.5f}, {v.get('lon', 0.0):.5f}",
            })

        st.dataframe(pd.DataFrame(table_rows), width="stretch", hide_index=True)
    else:
        st.info("No vehicles currently active in the network.")

    # BOTTOM ROW: SIGNAL TIMINGS TABLE
    st.markdown("---")
    st.subheader("🚦 Current Signal Timing Allocations & Telemetry")
    inter_table = []
    plan = res_snap["signal_plan"]

    for n_id, data in state_snap["intersections"].items():
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

    st.dataframe(pd.DataFrame(inter_table), width="stretch", hide_index=True)

# Render the real-time fragment
render_live_traffic_grid()
