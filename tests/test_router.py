"""
Unit tests for geo-registry, Dijkstra route optimization, and traffic color-coding.
"""

import pytest
from src.traffic.simulator import TrafficSimulator
from src.traffic.geo_registry import CITY_PRESETS, get_city_node_geo, get_all_city_places
from src.traffic.router import TrafficRouter


def test_geo_registry_presets():
    assert "Bengaluru Central CBD & Tech Corridor" in CITY_PRESETS
    assert "Mumbai South & BKC Corridor" in CITY_PRESETS
    assert "Delhi NCR Central & Connaught Place" in CITY_PRESETS
    assert "Hyderabad HITEC City & Financial District" in CITY_PRESETS

    node_a = get_city_node_geo("A", "Bengaluru Central CBD & Tech Corridor")
    assert "lat" in node_a and "lon" in node_a
    assert 12.0 < node_a["lat"] < 14.0
    assert 77.0 < node_a["lon"] < 78.0
    assert "MG Road" in node_a["google_name"]
    assert "560001" in node_a["formatted_address"]

    places = get_all_city_places("Bengaluru Central CBD & Tech Corridor", num_nodes=4)
    assert len(places) == 4
    assert "A" in places and "D" in places


def test_traffic_router_color_classification():
    heavy = TrafficRouter.get_traffic_status(0.80, queue_length=20)
    assert heavy["level"] == "heavy"
    assert heavy["color"] == "#ef4444"  # Red

    medium = TrafficRouter.get_traffic_status(0.50, queue_length=10)
    assert medium["level"] == "medium"
    assert medium["color"] == "#f59e0b"  # Yellow

    clear = TrafficRouter.get_traffic_status(0.20, queue_length=2)
    assert clear["level"] == "clear"
    assert clear["color"] == "#10b981"  # Green


def test_traffic_routing_computation():
    sim = TrafficSimulator(num_intersections=4, scenario="morning_peak", seed=42)
    for _ in range(5):
        sim.step()
    state = sim.get_state()

    router = TrafficRouter(sim, city_name="Bengaluru Central CBD & Tech Corridor")
    route = router.compute_route("A", "D", state, preference="fastest")

    assert route["found"] is True
    assert route["origin"] == "A"
    assert route["destination"] == "D"
    assert "MG Road" in route["origin_name"]
    assert "Richmond Circle" in route["destination_name"]
    assert len(route["path_nodes"]) >= 2
    assert route["total_distance_km"] > 0
    assert route["total_time_min"] > 0
    assert len(route["segments"]) >= 1
    assert "turn_by_turn" in route
    assert "google_maps_url" in route

    # Each segment must have a valid traffic color
    for seg in route["segments"]:
        assert seg["color"] in ("#ef4444", "#f59e0b", "#10b981")


def test_routing_same_origin_destination():
    sim = TrafficSimulator(num_intersections=4, scenario="normal")
    state = sim.get_state()
    router = TrafficRouter(sim)

    route = router.compute_route("A", "A", state)
    assert route["found"] is True
    assert route["total_distance_km"] == 0.0
    assert len(route["path_nodes"]) == 1


def test_resolve_place_user_text_inputs():
    from src.traffic.geo_registry import resolve_place, get_place_suggestions

    # Test direct node letters in Bengaluru
    n_id, data, msg = resolve_place("A", "Bengaluru Central CBD & Tech Corridor", num_nodes=4)
    assert n_id == "A"
    assert "MG Road" in data["google_name"]
    assert "560001" in data["formatted_address"]

    n_id, data, msg = resolve_place("Node B", "Bengaluru Central CBD & Tech Corridor", num_nodes=4)
    assert n_id == "B"
    assert "Brigade Road" in data["google_name"]

    # Test Indian Google Maps places entered by user
    n_id, data, msg = resolve_place("MG Road", "Bengaluru Central CBD & Tech Corridor", num_nodes=4)
    assert n_id == "A"

    n_id, data, msg = resolve_place("Brigade Road", "Bengaluru Central CBD & Tech Corridor", num_nodes=4)
    assert n_id == "B"

    n_id, data, msg = resolve_place("Cubbon Park", "Bengaluru Central CBD & Tech Corridor", num_nodes=4)
    assert n_id == "C"

    n_id, data, msg = resolve_place("Richmond Circle", "Bengaluru Central CBD & Tech Corridor", num_nodes=4)
    assert n_id == "D"

    # Test Mumbai Indian Google Maps places
    n_id, data, msg = resolve_place("CSMT", "Mumbai South & BKC Corridor", num_nodes=4)
    assert n_id == "A"
    assert "CSMT" in data["google_name"]

    n_id, data, msg = resolve_place("Gateway of India", "Mumbai South & BKC Corridor", num_nodes=4)
    assert n_id == "B"

    # Test Delhi Indian Google Maps places
    n_id, data, msg = resolve_place("Connaught Place", "Delhi NCR Central & Connaught Place", num_nodes=4)
    assert n_id == "A"
    assert "Connaught Place" in data["google_name"]

    n_id, data, msg = resolve_place("India Gate", "Delhi NCR Central & Connaught Place", num_nodes=4)
    assert n_id == "B"

    # Test Hyderabad Indian Google Maps places
    n_id, data, msg = resolve_place("Cyber Towers", "Hyderabad HITEC City & Financial District", num_nodes=4)
    assert n_id == "A"
    assert "Cyber Towers" in data["google_name"]

    # Test empty or invalid input
    n_id, data, msg = resolve_place("", "Bengaluru Central CBD & Tech Corridor", num_nodes=4)
    assert n_id is None

    n_id, data, msg = resolve_place("random non-existent galaxy 999", "Bengaluru Central CBD & Tech Corridor", num_nodes=4, enable_online_geocoding=False)
    assert n_id is None

    # Suggestions list
    suggs = get_place_suggestions("Bengaluru Central CBD & Tech Corridor", num_nodes=4)
    assert len(suggs) == 4
    assert suggs[0]["node_id"] == "A"
    assert "MG Road" in suggs[0]["google_name"]


def test_travel_time_eta_metrics():
    sim = TrafficSimulator(num_intersections=4, scenario="evening_peak", seed=42)
    for _ in range(3):
        sim.step()
    state = sim.get_state()
    router = TrafficRouter(sim, city_name="Bengaluru Central CBD & Tech Corridor")
    route = router.compute_route("A", "D", state, preference="fastest")

    assert "total_time_formatted" in route
    assert "min" in route["total_time_formatted"] or "sec" in route["total_time_formatted"]
    assert "arrival_time_ist" in route
    assert "IST" in route["arrival_time_ist"]
    assert "departure_time_ist" in route
    assert "IST" in route["departure_time_ist"]
    assert "free_flow_time_min" in route and route["free_flow_time_min"] > 0
    assert "delay_time_min" in route and route["delay_time_min"] >= 0
    assert "aqsa_savings_sec" in route and route["aqsa_savings_sec"] >= 0


def test_multi_destination_eta_matrix():
    sim = TrafficSimulator(num_intersections=4, scenario="normal", seed=42)
    state = sim.get_state()
    router = TrafficRouter(sim, city_name="Bengaluru Central CBD & Tech Corridor")

    etas = router.compute_all_destinations_eta("A", state)
    assert len(etas) == 3  # B, C, D (origin A excluded)

    for item in etas:
        assert item["origin_node"] == "A"
        assert item["destination_node"] in ("B", "C", "D")
        assert "travel_time_min" in item and item["travel_time_min"] > 0
        assert "travel_time_formatted" in item and ("min" in item["travel_time_formatted"] or "sec" in item["travel_time_formatted"])
        assert "arrival_time_ist" in item and "IST" in item["arrival_time_ist"]
        assert "distance_km" in item and item["distance_km"] > 0
        assert "condition" in item

    # Check sorting order: ascending by travel_time_min
    for i in range(len(etas) - 1):
        assert etas[i]["travel_time_min"] <= etas[i + 1]["travel_time_min"]


def test_vehicle_eta_properties():
    from src.traffic.vehicle import Vehicle

    v = Vehicle(
        id="TEST_01",
        vehicle_type="Car",
        origin="A",
        destination="B",
        current_edge=("A", "B"),
        position_on_edge=100.0,
        speed=10.0,  # 10 m/s = 36 km/h
        edge_length=300.0,
    )
    # Remaining distance: 200m at 10 m/s = 20s = 0.33 min
    assert 0.3 <= v.eta_destination_min <= 0.4
    assert "s" in v.eta_formatted or "m" in v.eta_formatted

    d = v.to_dict()
    assert "eta_destination" in d
    assert "eta_min" in d
    assert d["eta_destination"] == v.eta_formatted

