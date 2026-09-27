"""
Shortest-Path and Real-Time Traffic Routing Engine.
Calculates shortest and fastest paths across the smart city network,
predicts road segment congestion, and assigns traffic colors (Green, Yellow, Red).
"""

from typing import Dict, List, Tuple, Any, Optional
import networkx as nx
import numpy as np
from src.traffic.geo_registry import get_city_node_geo, CITY_PRESETS, DEFAULT_INDIAN_CITY


class TrafficRouter:
    """
    Computes optimal vehicle routes and evaluates real-time / predicted traffic conditions.
    """

    def __init__(self, simulator_or_network: Any, city_name: str = DEFAULT_INDIAN_CITY):
        self.city_name = city_name
        self.preset = CITY_PRESETS.get(city_name, CITY_PRESETS[DEFAULT_INDIAN_CITY])

        # Extract network graph from simulator or directly from network
        if hasattr(simulator_or_network, "network"):
            self.network = simulator_or_network.network
        else:
            self.network = simulator_or_network

    @staticmethod
    def get_traffic_status(congestion_index: float, queue_length: int = 0) -> Dict[str, Any]:
        """
        Classifies traffic into Green (Clear), Yellow (Medium), and Red (Heavy)
        as requested by the user.
        """
        if congestion_index >= 0.65 or queue_length >= 16:
            return {
                "level": "heavy",
                "color": "#ef4444",       # Vivid Red
                "label": "Heavy Traffic",
                "icon": "🔴",
                "avg_speed_kmh": 12.0,
                "description": "Severe congestion with queuing delays",
            }
        elif congestion_index >= 0.35 or queue_length >= 8:
            return {
                "level": "medium",
                "color": "#f59e0b",       # Vibrant Yellow / Amber
                "label": "Medium Traffic",
                "icon": "🟡",
                "avg_speed_kmh": 24.0,
                "description": "Moderate flow with minor stop-and-go delays",
            }
        else:
            return {
                "level": "clear",
                "color": "#10b981",       # Emerald Green
                "label": "Clear Road",
                "icon": "🟢",
                "avg_speed_kmh": 42.0,
                "description": "Free flowing traffic with minimal delays",
            }

    def compute_route(
        self,
        origin: str,
        destination: str,
        traffic_state: Dict[str, Any],
        preference: str = "fastest",  # "fastest" or "shortest"
        origin_geo: Optional[Dict[str, Any]] = None,
        dest_geo: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Finds the shortest or fastest route from origin to destination intersection.
        Returns path coordinates, segment traffic colors, ETA, distance, and guidance.
        """
        import urllib.parse

        if origin == destination:
            orig_g = origin_geo or get_city_node_geo(origin, self.city_name)
            dest_g = dest_geo or orig_g
            orig_name = orig_g.get("google_name", orig_g.get("name"))
            dest_name = dest_g.get("google_name", dest_g.get("name"))
            orig_addr = orig_g.get("formatted_address", orig_name)
            dest_addr = dest_g.get("formatted_address", dest_name)
            return {
                "found": True,
                "origin": origin,
                "destination": destination,
                "origin_name": orig_name,
                "destination_name": dest_name,
                "origin_address": orig_addr,
                "destination_address": dest_addr,
                "origin_coords": (orig_g["lat"], orig_g["lon"]),
                "destination_coords": (dest_g["lat"], dest_g["lon"]),
                "google_maps_url": f"https://www.google.com/maps/dir/?api=1&origin={urllib.parse.quote(orig_addr)}&destination={urllib.parse.quote(dest_addr)}&travelmode=driving",
                "path_nodes": [origin],
                "path_coords": [(orig_g["lat"], orig_g["lon"])],
                "total_distance_km": 0.0,
                "total_time_min": 0.0,
                "avg_speed_kmh": 0.0,
                "overall_condition": "Clear Road",
                "overall_color": "#10b981",
                "overall_icon": "🟢",
                "segments": [],
                "turn_by_turn": [
                    f"Direct corridor link: Proceed along <b>{orig_name}</b> toward <b>{dest_name}</b>.",
                    f"🏁 Arrive at Google Maps Destination: <b>{dest_name}</b> ({dest_addr}).",
                ],
            }

        # Build weighted routing graph using real network topology
        G = nx.DiGraph()
        intersections = traffic_state.get("intersections", {})

        # Distance between grid nodes in km
        base_dist_km = (self.network.block_length / 1000.0) if hasattr(self.network, "block_length") else 0.35

        for (u, v), edge_info in self.network.edge_data.items():
            # Only route through internal city intersections
            if "_" in u or "_" in v:
                continue

            node_data_v = intersections.get(v, {})
            cong_v = node_data_v.get("congestion_index", 0.3)
            q_v = node_data_v.get("queue_length", 5)
            wait_v = node_data_v.get("avg_waiting_time", 10.0)

            # Traffic classification
            traffic_info = self.get_traffic_status(cong_v, q_v)

            # Travel time calculation in seconds
            # Base free flow time + congestion delay + queuing penalty
            free_flow_sec = (base_dist_km / 40.0) * 3600.0  # 40 km/h free flow
            traffic_multiplier = 1.0 + 3.0 * (cong_v ** 2)
            queue_delay_sec = q_v * 1.5 + wait_v * 0.5
            segment_time_sec = free_flow_sec * traffic_multiplier + queue_delay_sec

            G.add_edge(
                u,
                v,
                distance_km=base_dist_km,
                time_sec=segment_time_sec,
                congestion=cong_v,
                queue=q_v,
                traffic_info=traffic_info,
                direction=edge_info.get("direction", "E"),
            )

        # Ensure path exists
        if not G.has_node(origin) or not G.has_node(destination):
            return {"found": False, "error": f"Selected intersection {origin} or {destination} not in active network."}

        weight_attr = "time_sec" if preference == "fastest" else "distance_km"
        try:
            path_nodes = nx.shortest_path(G, source=origin, target=destination, weight=weight_attr)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            # Fallback to shortest path if fastest is disconnected
            try:
                path_nodes = nx.shortest_path(G, source=origin, target=destination)
            except Exception:
                return {"found": False, "error": f"No road connection found from Node {origin} to Node {destination}."}

        # Assemble route geometry, telemetry, and segment traffic colors
        segments = []
        path_coords = []
        total_dist_km = 0.0
        total_time_sec = 0.0
        worst_congestion = 0.0
        turn_by_turn = []

        for i in range(len(path_nodes) - 1):
            u = path_nodes[i]
            v = path_nodes[i + 1]

            edge = G[u][v]
            dist_km = edge["distance_km"]
            time_sec = edge["time_sec"]
            cong = edge["congestion"]
            traffic = edge["traffic_info"]

            u_geo = get_city_node_geo(u, self.city_name)
            v_geo = get_city_node_geo(v, self.city_name)

            if i == 0:
                path_coords.append((u_geo["lat"], u_geo["lon"]))
            path_coords.append((v_geo["lat"], v_geo["lon"]))

            total_dist_km += dist_km
            total_time_sec += time_sec
            worst_congestion = max(worst_congestion, cong)

            segments.append({
                "from_node": u,
                "to_node": v,
                "from_name": u_geo["name"],
                "to_name": v_geo["name"],
                "from_coords": (u_geo["lat"], u_geo["lon"]),
                "to_coords": (v_geo["lat"], v_geo["lon"]),
                "distance_km": dist_km,
                "time_sec": time_sec,
                "congestion_index": cong,
                "queue_veh": edge["queue"],
                "traffic_level": traffic["level"],
                "color": traffic["color"],      # Red / Yellow / Green
                "label": traffic["label"],
                "icon": traffic["icon"],
            })

            # Turn by turn step instruction
            dir_text = {"E": "Eastbound", "W": "Westbound", "N": "Northbound", "S": "Southbound"}.get(edge["direction"], "forward")
            u_gname = u_geo.get("google_name", u_geo["name"])
            v_gname = v_geo.get("google_name", v_geo["name"])
            step_instruction = (
                f"Step {i+1}: From <b>{u_gname}</b>, proceed {dir_text} "
                f"toward <b>{v_gname}</b> — {traffic['icon']} <b>{traffic['label']}</b> "
                f"({dist_km*1000:.0f}m, ~{time_sec/60:.1f} min)"
            )
            turn_by_turn.append(step_instruction)

        def_dest_geo = get_city_node_geo(destination, self.city_name)
        def_orig_geo = get_city_node_geo(origin, self.city_name)
        dest_g = dest_geo or def_dest_geo
        orig_g = origin_geo or def_orig_geo
        dest_gname = dest_g.get("google_name", dest_g.get("name"))
        orig_gname = orig_g.get("google_name", orig_g.get("name"))
        dest_addr = dest_g.get("formatted_address", dest_gname)
        orig_addr = orig_g.get("formatted_address", orig_gname)

        turn_by_turn.append(f"🏁 Arrive at Google Maps Destination: <b>{dest_gname}</b> ({dest_addr}).")

        # Overall route traffic condition
        overall_traffic = self.get_traffic_status(worst_congestion)
        total_time_min = max(0.8, total_time_sec / 60.0)
        avg_speed = (total_dist_km / (total_time_sec / 3600.0)) if total_time_sec > 0 else 30.0

        import urllib.parse
        g_maps_directions_url = (
            f"https://www.google.com/maps/dir/?api=1&origin="
            f"{urllib.parse.quote(orig_addr)}&destination="
            f"{urllib.parse.quote(dest_addr)}&travelmode=driving"
        )

        return {
            "found": True,
            "origin": origin,
            "destination": destination,
            "origin_name": orig_gname,
            "destination_name": dest_gname,
            "origin_address": orig_addr,
            "destination_address": dest_addr,
            "origin_coords": (orig_g["lat"], orig_g["lon"]),
            "destination_coords": (dest_g["lat"], dest_g["lon"]),
            "google_maps_url": g_maps_directions_url,
            "path_nodes": path_nodes,
            "path_coords": path_coords,
            "total_distance_km": round(total_dist_km, 2),
            "total_time_min": round(total_time_min, 1),
            "avg_speed_kmh": round(avg_speed, 1),
            "overall_condition": overall_traffic["label"],
            "overall_color": overall_traffic["color"],
            "overall_icon": overall_traffic["icon"],
            "segments": segments,
            "turn_by_turn": turn_by_turn,
        }
