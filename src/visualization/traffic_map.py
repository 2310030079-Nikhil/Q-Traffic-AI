"""
Interactive Plotly Real-Time City Map Visualizer.
Renders real-world Google Maps / OpenStreetMap street tiles, live traffic conditions
(Green = Clear, Yellow = Medium, Red = Heavy), signal states, and shortest-path routing.
"""

from typing import Dict, Any, List, Optional
import plotly.graph_objects as go
import numpy as np
from src.traffic.geo_registry import get_city_node_geo, CITY_PRESETS, DEFAULT_INDIAN_CITY


class TrafficMapVisualizer:
    """
    Renders topological 2D and real-world geographic smart city traffic maps
    with live traffic color-coding, signal states, and route navigation.
    """

    @staticmethod
    def create_network_figure(
        traffic_state: Dict[str, Any],
        selected_nodes: Optional[List[str]] = None,
        node_positions: Optional[Dict[str, Any]] = None,
        active_route: Optional[Dict[str, Any]] = None,
        map_style: str = "open-street-map",  # 'open-street-map', 'carto-darkmatter', 'carto-positron', 'abstract'
        city_name: str = DEFAULT_INDIAN_CITY,
        show_all_traffic: bool = True,
    ) -> go.Figure:
        """
        Creates an interactive Plotly map. If map_style is 'abstract', renders a 2D canvas.
        Otherwise, renders a real-world Google Maps / OpenStreetMap geographic road map.
        """
        intersections = traffic_state.get("intersections", {})
        num_nodes = len(intersections)
        selected_set = set(selected_nodes if selected_nodes else [])

        # If user explicitly wants the 2D abstract schematic
        if map_style == "abstract":
            return TrafficMapVisualizer._create_abstract_figure(
                traffic_state=traffic_state,
                selected_set=selected_set,
                active_route=active_route,
                node_positions=node_positions,
            )

        # Real-World Geographic Map (Google Maps / OpenStreetMap style)
        return TrafficMapVisualizer._create_geo_figure(
            traffic_state=traffic_state,
            selected_set=selected_set,
            active_route=active_route,
            map_style=map_style,
            city_name=city_name,
            show_all_traffic=show_all_traffic,
        )

    @staticmethod
    def _create_geo_figure(
        traffic_state: Dict[str, Any],
        selected_set: set,
        active_route: Optional[Dict[str, Any]],
        map_style: str,
        city_name: str,
        show_all_traffic: bool = True,
    ) -> go.Figure:
        """Constructs geographic map with real-world street tiles, road lines, and route navigation."""
        fig = go.Figure()
        ScatterClass = getattr(go, "Scattermap", go.Scattermapbox)

        preset = CITY_PRESETS.get(city_name, CITY_PRESETS[DEFAULT_INDIAN_CITY])
        center_lat, center_lon = preset["city_center"]
        zoom_level = preset.get("zoom", 14.8)

        intersections = traffic_state.get("intersections", {})
        node_ids = list(intersections.keys())

        # Determine connections between adjacent grid nodes
        cols = 3 if len(node_ids) >= 6 else 2
        conn_pairs = []
        for idx, u in enumerate(node_ids):
            r = idx // cols
            c = idx % cols
            # East neighbor
            if c + 1 < cols and (idx + 1) < len(node_ids):
                v_east = node_ids[idx + 1]
                conn_pairs.append((u, v_east))
            # South neighbor
            if (idx + cols) < len(node_ids):
                v_south = node_ids[idx + cols]
                conn_pairs.append((u, v_south))

        # 1. Draw Road Network Links with Real-Time Traffic Colors
        # Red = Heavy Traffic, Yellow = Medium Traffic, Green = Clear Road
        green_lats, green_lons, green_texts = [], [], []
        yellow_lats, yellow_lons, yellow_texts = [], [], []
        red_lats, red_lons, red_texts = [], [], []

        for u, v in conn_pairs:
            u_geo = get_city_node_geo(u, city_name)
            v_geo = get_city_node_geo(v, city_name)

            data_u = intersections.get(u, {})
            data_v = intersections.get(v, {})

            # Segment congestion index
            avg_cong = (data_u.get("congestion_index", 0.3) + data_v.get("congestion_index", 0.3)) / 2.0
            avg_queue = (data_u.get("queue_length", 5) + data_v.get("queue_length", 5)) // 2

            hover_text = (
                f"<b>Corridor: {u_geo['name']} ➔ {v_geo['name']}</b><br>"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━<br>"
                f"Traffic State: <b>{'🔴 HEAVY' if avg_cong >= 0.65 else ('🟡 MEDIUM' if avg_cong >= 0.35 else '🟢 CLEAR')}</b><br>"
                f"Congestion Index: <b>{avg_cong*100:.1f}%</b><br>"
                f"Queue Buildup: <b>{avg_queue} vehicles</b>"
            )

            if avg_cong >= 0.65:
                red_lats.extend([u_geo["lat"], v_geo["lat"], None])
                red_lons.extend([u_geo["lon"], v_geo["lon"], None])
                red_texts.extend([hover_text, hover_text, None])
            elif avg_cong >= 0.35:
                yellow_lats.extend([u_geo["lat"], v_geo["lat"], None])
                yellow_lons.extend([u_geo["lon"], v_geo["lon"], None])
                yellow_texts.extend([hover_text, hover_text, None])
            else:
                green_lats.extend([u_geo["lat"], v_geo["lat"], None])
                green_lons.extend([u_geo["lon"], v_geo["lon"], None])
                green_texts.extend([hover_text, hover_text, None])

        # Add traffic road layers
        if show_all_traffic or not active_route:
            if green_lats:
                fig.add_trace(ScatterClass(
                    lat=green_lats,
                    lon=green_lons,
                    mode="lines",
                    line=dict(width=6, color="#10b981"),
                    name="🟢 Clear Traffic",
                    hoverinfo="text",
                    hovertext=green_texts,
                ))

            if yellow_lats:
                fig.add_trace(ScatterClass(
                    lat=yellow_lats,
                    lon=yellow_lons,
                    mode="lines",
                    line=dict(width=6.5, color="#f59e0b"),
                    name="🟡 Medium Traffic",
                    hoverinfo="text",
                    hovertext=yellow_texts,
                ))

            if red_lats:
                fig.add_trace(ScatterClass(
                    lat=red_lats,
                    lon=red_lons,
                    mode="lines",
                    line=dict(width=7, color="#ef4444"),
                    name="🔴 Heavy Traffic",
                    hoverinfo="text",
                    hovertext=red_texts,
                ))

        # 2. Draw Active Navigation Shortest Route (if user searched/entered places)
        if active_route and active_route.get("found"):
            path_nodes = active_route["path_nodes"]
            segments = active_route.get("segments", [])

            # Route Underlay Glow (Casing)
            route_lats = [c[0] for c in active_route["path_coords"]]
            route_lons = [c[1] for c in active_route["path_coords"]]

            fig.add_trace(ScatterClass(
                lat=route_lats,
                lon=route_lons,
                mode="lines",
                line=dict(width=13, color="#00f2fe"),
                name="🚀 Shortest Navigation Path",
                hoverinfo="text",
                hovertext=f"Selected Route: Node {active_route['origin']} ➔ Node {active_route['destination']} (ETA: {active_route['total_time_min']:.1f} min)",
            ))

            # Segment-by-segment predicted traffic overlay on the route
            for seg in segments:
                from_c = seg["from_coords"]
                to_c = seg["to_coords"]
                seg_color = seg["color"]  # Red, Yellow, or Green
                seg_label = seg["label"]

                fig.add_trace(ScatterClass(
                    lat=[from_c[0], to_c[0]],
                    lon=[from_c[1], to_c[1]],
                    mode="lines",
                    line=dict(width=7, color=seg_color),
                    name=f"Route Segment: {seg['from_node']} ➔ {seg['to_node']} ({seg_label})",
                    hoverinfo="text",
                    hovertext=(
                        f"<b>{seg['from_name']} ➔ {seg['to_name']}</b><br>"
                        f"Predicted Traffic: <b>{seg['icon']} {seg_label}</b><br>"
                        f"Congestion: <b>{seg['congestion_index']*100:.1f}%</b> | Queue: <b>{seg['queue_veh']} veh</b><br>"
                        f"Distance: <b>{seg['distance_km']*1000:.0f} m</b> | Est. Time: <b>{seg['time_sec']/60:.1f} min</b>"
                    ),
                    showlegend=False,
                ))

            # Origin Pin Marker
            origin_geo = get_city_node_geo(active_route["origin"], city_name)
            orig_gname = origin_geo.get("google_name", origin_geo["name"])
            orig_addr = origin_geo.get("formatted_address", "")
            fig.add_trace(ScatterClass(
                lat=[origin_geo["lat"]],
                lon=[origin_geo["lon"]],
                mode="markers+text",
                marker=dict(size=22, color="#10b981", symbol="circle"),
                text=[f"📍 <b>START: {orig_gname}</b>"],
                textposition="top center",
                name="Start Origin",
                hoverinfo="text",
                hovertext=f"<b>📍 Google Maps Origin: {orig_gname}</b><br>{orig_addr}",
            ))

            # Destination Pin Marker
            dest_geo = get_city_node_geo(active_route["destination"], city_name)
            dest_gname = dest_geo.get("google_name", dest_geo["name"])
            dest_addr = dest_geo.get("formatted_address", "")
            fig.add_trace(ScatterClass(
                lat=[dest_geo["lat"]],
                lon=[dest_geo["lon"]],
                mode="markers+text",
                marker=dict(size=24, color="#ef4444", symbol="circle"),
                text=[f"🏁 <b>END: {dest_gname}</b>"],
                textposition="bottom center",
                name="Destination",
                hoverinfo="text",
                hovertext=f"<b>🏁 Google Maps Destination: {dest_gname}</b><br>{dest_addr}",
            ))

        # 3. Draw Smart City Signal Intersections
        node_lats, node_lons = [], []
        node_sizes, node_colors, node_texts, hover_texts = [], [], [], []

        for n_id in node_ids:
            geo = get_city_node_geo(n_id, city_name)
            node_lats.append(geo["lat"])
            node_lons.append(geo["lon"])

            data = intersections.get(n_id, {})
            q = data.get("queue_length", 10)
            wait = data.get("avg_waiting_time", 15.0)
            cong = data.get("congestion_index", 0.3)
            phase = data.get("current_phase", "NS_GREEN")
            g_ns = data.get("green_ns", 27.0)
            g_ew = data.get("green_ew", 27.0)

            is_selected = n_id in selected_set

            # Node size reflecting queue
            node_sizes.append(min(36, max(22, int(20 + q * 0.4))))

            # Node color
            if is_selected:
                node_colors.append("#00f2fe")  # Glowing Cyan for AQSA critical
            elif cong < 0.35:
                node_colors.append("#10b981")  # Green
            elif cong < 0.65:
                node_colors.append("#f59e0b")  # Yellow
            else:
                node_colors.append("#ef4444")  # Red

            place_label = geo.get("google_name", geo["name"])
            node_texts.append(f"<b>{place_label}</b>")

            badge = "⚛ AQSA CRITICAL (QUANTUM)" if is_selected else "⚪ HEURISTIC SIGNAL"
            phase_state = "🟢 N-S Green | 🔴 E-W Red" if "NS" in phase else "🔴 N-S Red | 🟢 E-W Green"

            hover_texts.append(
                f"<b>📍 {place_label}</b><br>"
                f"Address: <i>{geo.get('formatted_address', geo['name'])}</i><br>"
                f"Cross Streets: {geo.get('street_intersection', geo['name'])}<br>"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━<br>"
                f"Status: <b>{badge}</b><br>"
                f"Active Signal Phase: <b>{phase_state}</b><br>"
                f"Queue Length: <b>{q} vehicles</b><br>"
                f"Average Wait: <b>{wait:.1f} s</b><br>"
                f"Congestion Index: <b>{cong*100:.1f}%</b><br>"
                f"AQSA Timings: <b>N-S {g_ns:.0f}s | E-W {g_ew:.0f}s</b>"
            )

        fig.add_trace(ScatterClass(
            lat=node_lats,
            lon=node_lons,
            mode="markers+text",
            marker=dict(size=node_sizes, color=node_colors, opacity=0.92),
            text=node_texts,
            textposition="middle right",
            hovertext=hover_texts,
            hoverinfo="text",
            name="🚦 Signal Intersections",
        ))

        # Mapbox / Maplibre Layout Configuration
        layout_dict = dict(
            style=map_style,
            center=dict(lat=center_lat, lon=center_lon),
            zoom=zoom_level,
        )

        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            height=530,
            paper_bgcolor="#070b14",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.01,
                xanchor="center",
                x=0.5,
                bgcolor="rgba(15, 23, 42, 0.85)",
                font=dict(color="#cbd5e1", size=11),
                bordercolor="rgba(56, 189, 248, 0.25)",
                borderwidth=1,
            ),
        )

        # Handle Scattermap vs Scattermapbox attribute naming in Plotly
        if hasattr(fig.layout, "map"):
            fig.update_layout(map=layout_dict)
        else:
            fig.update_layout(mapbox=layout_dict)

        return fig

    @staticmethod
    def _create_abstract_figure(
        traffic_state: Dict[str, Any],
        selected_set: set,
        active_route: Optional[Dict[str, Any]],
        node_positions: Optional[Dict[str, Any]],
    ) -> go.Figure:
        """Fallback 2D cartesian abstract schematic view."""
        intersections = traffic_state.get("intersections", {})
        num_nodes = len(intersections)

        if not node_positions:
            cols = 3 if num_nodes == 9 else (3 if num_nodes == 6 else 2)
            rows = num_nodes // cols
            node_positions = {}
            for idx, n_id in enumerate(intersections.keys()):
                r = idx // cols
                c = idx % cols
                node_positions[n_id] = (c * 200.0, (rows - 1 - r) * 200.0)

        fig = go.Figure()
        edge_x, edge_y = [], []
        node_keys = list(node_positions.keys())

        for i, u in enumerate(node_keys):
            for j, v in enumerate(node_keys):
                if i < j:
                    pos_u = node_positions[u]
                    pos_v = node_positions[v]
                    if np.hypot(pos_u[0] - pos_v[0], pos_u[1] - pos_v[1]) <= 210.0:
                        edge_x.extend([pos_u[0], pos_v[0], None])
                        edge_y.extend([pos_u[1], pos_v[1], None])

        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=7, color="#1e293b"),
            hoverinfo="none", mode="lines", showlegend=False
        ))

        node_x, node_y, node_sizes, node_colors, node_texts, hover_texts = [], [], [], [], [], []
        for n_id, pos in node_positions.items():
            node_x.append(pos[0])
            node_y.append(pos[1])
            data = intersections.get(n_id, {})
            cong = data.get("congestion_index", 0.3)
            q = data.get("queue_length", 10)
            is_selected = n_id in selected_set

            node_sizes.append(min(52, max(28, int(24 + q * 0.4))))
            color = "#00f2fe" if is_selected else ("#ef4444" if cong >= 0.65 else ("#f59e0b" if cong >= 0.35 else "#10b981"))
            node_colors.append(color)
            node_texts.append(f"<b>{n_id}</b>")
            hover_texts.append(f"Node {n_id}: Congestion {cong*100:.1f}%, Queue {q} veh")

        fig.add_trace(go.Scatter(
            x=node_x, y=node_y, mode="markers+text",
            marker=dict(size=node_sizes, color=node_colors),
            text=node_texts, hovertext=hover_texts, hoverinfo="text", showlegend=False
        ))

        fig.update_layout(
            paper_bgcolor="#070b14", plot_bgcolor="#070b14",
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, scaleanchor="x", scaleratio=1),
            height=460,
        )
        return fig
