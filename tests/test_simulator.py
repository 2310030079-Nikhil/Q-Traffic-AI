"""
Unit tests for Traffic Simulator, Network Topology, and Signal Controllers.
"""

import pytest
from src.traffic.network import TrafficNetwork
from src.traffic.signal import TrafficSignal, SignalPhase
from src.traffic.simulator import TrafficSimulator


def test_signal_controller():
    sig = TrafficSignal(intersection_id="A", cycle_length=60.0, green_ns=25.0, green_ew=25.0, yellow_duration=3.0)
    assert sig.current_phase == SignalPhase.NS_GREEN
    assert sig.is_green_for_approach("N") is True
    assert sig.is_green_for_approach("E") is False

    # Advance beyond NS green -> should enter NS yellow
    sig.update(26.0)
    assert sig.current_phase == SignalPhase.NS_YELLOW


def test_network_topology_sizes():
    for n in [4, 6, 9]:
        net = TrafficNetwork(num_intersections=n)
        assert len(net.get_intersection_ids()) == n
        assert len(net.signals) == n
        # Check that internal edges were generated
        assert len(net.edge_data) > 0


def test_simulator_stepping_and_scenarios():
    sim = TrafficSimulator(num_intersections=4, scenario="morning_peak", seed=42)
    state0 = sim.get_state()
    assert state0["num_intersections"] == 4
    assert state0["total_vehicles"] > 0

    state1 = sim.step()
    assert state1["step"] == 1
    assert state1["timestamp"] > 0
    assert "A" in state1["intersections"]
    assert state1["intersections"]["A"]["queue_length"] >= 0


def test_simulator_apply_plan():
    sim = TrafficSimulator(num_intersections=4, seed=42)
    custom_plan = {
        "A": {"green_ns": 38.0, "green_ew": 18.0},
        "B": {"green_ns": 18.0, "green_ew": 38.0},
    }
    sim.apply_signal_plan(custom_plan)
    sig_a = sim.network.signals["A"]
    assert sig_a.green_ns == 38.0
    assert sig_a.green_ew == 18.0


def test_tracked_vehicles_and_fleet():
    sim = TrafficSimulator(num_intersections=4, scenario="morning_peak", seed=42)
    state = sim.get_state()
    assert "tracked_vehicles" in state
    assert len(state["tracked_vehicles"]) > 0
    first_veh = state["tracked_vehicles"][0]
    assert "id" in first_veh
    assert "lat" in first_veh
    assert "lon" in first_veh
    assert "speed_kmh" in first_veh
    assert "type" in first_veh

    fleet = sim.get_fleet_summary()
    assert fleet["total_tracked"] > 0
    assert "Car" in fleet["by_type"]


def test_emergency_vehicle_dispatch():
    sim = TrafficSimulator(num_intersections=4, seed=42)
    amb = sim.spawn_emergency_vehicle()
    assert amb.is_emergency is True
    assert amb.vehicle_type == "Ambulance"
    assert sim.last_emergency_id == amb.id
    sim.step()
    state = sim.get_state()
    assert any(v["is_emergency"] for v in state["tracked_vehicles"])


def test_live_traffic_feed_manager():
    from src.traffic.live_api import LiveTrafficFeedManager
    feed = LiveTrafficFeedManager.get_autonomous_realtime_feed("Bengaluru Central CBD & Tech Corridor")
    assert "congestion_index" in feed
    assert 0.0 <= feed["congestion_index"] <= 1.0
    assert "timestamp_ist" in feed
    assert len(feed["arterial_corridors"]) > 0

