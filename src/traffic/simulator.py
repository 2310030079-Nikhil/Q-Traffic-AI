"""
Realistic discrete-time traffic simulator for urban grid networks.
Supports 4, 6, and 9 intersections with dynamic traffic scenarios.
"""

from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import random
from src.traffic.network import TrafficNetwork
from src.traffic.signal import SignalPhase


class TrafficSimulator:
    """
    Simulates vehicle propagation, signal control, queue dynamics, and delays across network.
    """

    SCENARIOS = {
        "normal": {"base_rate": 0.35, "desc": "Balanced moderate traffic demand across city grid"},
        "morning_peak": {"base_rate": 0.65, "ew_bias": 2.2, "desc": "High inbound East-West commuter traffic"},
        "evening_peak": {"base_rate": 0.65, "ns_bias": 2.2, "desc": "Heavy North-South outbound corridor flow"},
        "traffic_spike": {"base_rate": 0.35, "spike_node": "A", "spike_rate": 2.8, "desc": "Sudden localized traffic surge at key hub"},
        "uneven": {"base_rate": 0.30, "arterial_bias": 2.5, "desc": "Heavily saturated main corridor with light feeder lanes"},
        "high_uncertainty": {"base_rate": 0.45, "noise_scale": 1.8, "desc": "Burst-prone stochastic arrivals with high variance"},
    }

    def __init__(
        self,
        num_intersections: int = 4,
        scenario: str = "normal",
        seed: Optional[int] = 42,
    ):
        self.num_intersections = num_intersections
        self.scenario = scenario
        self.seed = seed
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)

        self.network = TrafficNetwork(num_intersections=num_intersections)
        self.time: float = 0.0
        self.dt: float = 2.0  # simulation step in seconds
        self.step_count: int = 0

        # Performance accumulators
        self.completed_trips: int = 0
        self.total_completed_wait: float = 0.0
        self.history: List[Dict[str, Any]] = []

        # Initialize network state
        self._initialize_traffic()

    def _initialize_traffic(self):
        """Pre-populate network edges with realistic initial vehicle queues."""
        for edge_key, data in self.network.edge_data.items():
            base_init = np.random.randint(4, 12)
            if self.scenario == "morning_peak" and data["direction"] in ("E", "W"):
                base_init = int(base_init * 1.8)
            elif self.scenario == "evening_peak" and data["direction"] in ("N", "S"):
                base_init = int(base_init * 1.8)
            elif self.scenario == "traffic_spike" and data["to"] == "A":
                base_init = int(base_init * 2.5)

            data["queued_vehicles"] = min(data["capacity"] - 2, base_init)
            data["moving_vehicles"] = np.random.randint(2, 6)
            data["avg_waiting_time"] = float(np.random.uniform(8.0, 25.0))

    def set_scenario(self, scenario: str):
        if scenario in self.SCENARIOS:
            self.scenario = scenario

    def apply_signal_plan(self, plan: Dict[str, Dict[str, float]]):
        """
        Apply newly optimized green durations to network traffic signals.
        plan format: { 'A': {'green_ns': 35.0, 'green_ew': 25.0}, ... }
        """
        for node_id, durations in plan.items():
            if node_id in self.network.signals:
                self.network.signals[node_id].set_durations(
                    green_ns=durations.get("green_ns", 27.0),
                    green_ew=durations.get("green_ew", 27.0),
                )

    def step(self, signal_actions: Optional[Dict[str, Dict[str, float]]] = None) -> Dict[str, Any]:
        """
        Execute one discrete simulation step of dt seconds.
        """
        if signal_actions:
            self.apply_signal_plan(signal_actions)

        # 1. Update all traffic signals
        for signal in self.network.signals.values():
            signal.update(self.dt)

        scenario_cfg = self.SCENARIOS.get(self.scenario, self.SCENARIOS["normal"])
        base_arrival = scenario_cfg.get("base_rate", 0.35)

        # 2. Process vehicle generation at ingress edges
        for (u, v), edge in self.network.edge_data.items():
            if u.startswith("IN_"):
                # Determine rate for this ingress
                rate = base_arrival
                if self.scenario == "morning_peak" and edge["direction"] in ("E", "W"):
                    rate *= scenario_cfg.get("ew_bias", 2.0)
                elif self.scenario == "evening_peak" and edge["direction"] in ("N", "S"):
                    rate *= scenario_cfg.get("ns_bias", 2.0)
                elif self.scenario == "traffic_spike" and v == scenario_cfg.get("spike_node", "A"):
                    rate *= scenario_cfg.get("spike_rate", 2.5)
                elif self.scenario == "high_uncertainty":
                    noise = np.random.uniform(0.3, scenario_cfg.get("noise_scale", 1.8))
                    rate *= noise

                # Poisson arrivals
                new_arrivals = np.random.poisson(rate * (self.dt / 2.0))
                available_space = max(0, edge["capacity"] - (edge["queued_vehicles"] + edge["moving_vehicles"]))
                admitted = min(new_arrivals, available_space)
                edge["moving_vehicles"] += admitted

        # 3. Simulate vehicle progression and queuing on all edges
        for (u, v), edge in self.network.edge_data.items():
            # Moving vehicles advance toward intersection queue
            if edge["moving_vehicles"] > 0:
                progression_rate = 0.45 * (self.dt / 2.0)
                becoming_queued = int(np.random.binomial(edge["moving_vehicles"], min(1.0, progression_rate)))
                edge["moving_vehicles"] -= becoming_queued
                edge["queued_vehicles"] += becoming_queued

            # Vehicles in queue accumulate wait time
            if edge["queued_vehicles"] > 0:
                edge["avg_waiting_time"] += self.dt * 0.95
            else:
                edge["avg_waiting_time"] = max(0.0, edge["avg_waiting_time"] - self.dt * 0.5)

            # Check if vehicles can discharge through downstream intersection v
            if v in self.network.signals:
                signal = self.network.signals[v]
                is_green = signal.is_green_for_approach(edge["direction"])
                if is_green and edge["queued_vehicles"] > 0:
                    # Saturation discharge: ~0.55 veh/sec on green
                    discharge_potential = int(np.random.poisson(0.55 * self.dt))
                    discharged = min(edge["queued_vehicles"], discharge_potential)
                    edge["queued_vehicles"] -= discharged
                    edge["avg_waiting_time"] = max(0.0, edge["avg_waiting_time"] - (discharged * 1.5))

                    # Route discharged vehicles to outgoing links or exit
                    outgoing = self.network.get_outgoing_edges(v)
                    if outgoing:
                        out_edge_key = random.choice(outgoing)
                        out_data = self.network.edge_data[out_edge_key]
                        if out_data["to"].startswith("OUT_"):
                            # Vehicle departs network
                            self.completed_trips += discharged
                            self.total_completed_wait += discharged * edge["avg_waiting_time"]
                        else:
                            # Forwarded to next internal road link
                            out_data["moving_vehicles"] += discharged

        # 4. Advance clock
        self.time += self.dt
        self.step_count += 1

        # 5. Harvest instantaneous state snapshot
        state = self.get_state()
        self.history.append(state)
        return state

    def get_state(self) -> Dict[str, Any]:
        """
        Aggregate comprehensive traffic metrics across all intersections.
        """
        intersection_stats: Dict[str, Dict[str, Any]] = {}
        total_queued = 0
        total_volume = 0
        wait_times: List[float] = []

        for node_id in self.network.get_intersection_ids():
            in_edges = self.network.get_incoming_edges(node_id)
            node_queue = 0
            node_volume = 0
            node_capacity = 0
            node_waits: List[float] = []
            speeds: List[float] = []

            for edge_key in in_edges:
                edge = self.network.edge_data[edge_key]
                node_queue += edge["queued_vehicles"]
                vol = edge["queued_vehicles"] + edge["moving_vehicles"]
                node_volume += vol
                node_capacity += edge["capacity"]
                if edge["queued_vehicles"] > 0:
                    node_waits.append(edge["avg_waiting_time"])
                # Speed drops as occupancy increases
                occ = vol / max(1, edge["capacity"])
                speed = max(2.5, edge["speed_limit"] * (1.0 - 0.75 * occ))
                speeds.append(speed)

            avg_wait = float(np.mean(node_waits)) if node_waits else 0.0
            avg_speed = float(np.mean(speeds)) if speeds else 12.0
            occupancy = float(node_volume / max(1, node_capacity))
            density = float(node_volume / (len(in_edges) * (self.network.block_length / 1000.0)))  # veh/km

            # Normalized Congestion Index (0.0 to 1.0)
            congestion_index = min(1.0, 0.45 * occupancy + 0.35 * (node_queue / max(1, node_capacity)) + 0.20 * (avg_wait / 60.0))

            signal = self.network.signals[node_id]

            intersection_stats[node_id] = {
                "intersection_id": node_id,
                "volume": int(node_volume),
                "queue_length": int(node_queue),
                "avg_waiting_time": round(avg_wait, 1),
                "occupancy": round(occupancy, 3),
                "density": round(density, 1),
                "avg_speed": round(avg_speed, 1),
                "congestion_index": round(congestion_index, 3),
                "current_phase": signal.current_phase.name,
                "green_ns": round(signal.green_ns, 1),
                "green_ew": round(signal.green_ew, 1),
                "cycle_length": round(signal.cycle_length, 1),
            }

            total_queued += node_queue
            total_volume += node_volume
            if avg_wait > 0:
                wait_times.append(avg_wait)

        global_avg_wait = float(np.mean(wait_times)) if wait_times else 0.0
        global_congestion = float(np.mean([s["congestion_index"] for s in intersection_stats.values()]))
        throughput = round((self.completed_trips / max(1.0, self.time)) * 60.0, 1)  # vehicles per minute

        return {
            "timestamp": round(self.time, 1),
            "step": self.step_count,
            "scenario": self.scenario,
            "num_intersections": self.num_intersections,
            "total_vehicles": total_volume,
            "total_queued": total_queued,
            "global_avg_wait": round(global_avg_wait, 1),
            "global_congestion": round(global_congestion, 3),
            "throughput_veh_per_min": throughput,
            "intersections": intersection_stats,
        }

    def reset(self, scenario: Optional[str] = None):
        """Reset simulation state and re-initialize traffic."""
        if scenario:
            self.scenario = scenario
        self.time = 0.0
        self.step_count = 0
        self.completed_trips = 0
        self.total_completed_wait = 0.0
        self.history.clear()
        self.network = TrafficNetwork(num_intersections=self.num_intersections)
        self._initialize_traffic()
