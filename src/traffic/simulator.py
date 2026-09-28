"""
Realistic discrete-time traffic simulator for urban grid networks.
Supports 4, 6, and 9 intersections with dynamic traffic scenarios,
multi-modal discrete vehicle tracking, GPS kinematics, and emergency preemption.
"""

from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import random
from src.traffic.network import TrafficNetwork
from src.traffic.signal import SignalPhase
from src.traffic.vehicle import Vehicle, VEHICLE_TYPE_CONFIG
from src.traffic.geo_registry import get_city_node_geo, DEFAULT_INDIAN_CITY


class TrafficSimulator:
    """
    Simulates vehicle propagation, signal control, queue dynamics, and delays across network.
    Maintains both aggregate continuum edge states and discrete GPS-tracked vehicle entities.
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
        city_name: str = DEFAULT_INDIAN_CITY,
    ):
        self.num_intersections = num_intersections
        self.scenario = scenario
        self.seed = seed
        self.city_name = city_name
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

        # Discrete vehicle fleet tracking
        self.vehicles: Dict[str, Vehicle] = {}
        self.vehicle_counter: int = 100
        self.emergency_preemption_active: bool = False
        self.last_emergency_id: Optional[str] = None

        # Initialize network state and vehicles
        self._initialize_traffic()

    def _create_vehicle(
        self,
        edge_key: Tuple[str, str],
        is_queued: bool = False,
        progress: float = 0.0,
        vehicle_type: Optional[str] = None,
    ) -> Vehicle:
        """Helper to instantiate and register a tracked vehicle on a road link."""
        self.vehicle_counter += 1
        if vehicle_type is None:
            # Multi-modal distribution for Indian metropolitan traffic
            r = random.random()
            if r < 0.04:
                vtype = "Ambulance"
            elif r < 0.16:
                vtype = "Bus"
            elif r < 0.36:
                vtype = "EV Taxi"
            elif r < 0.50:
                vtype = "Auto Rickshaw"
            else:
                vtype = "Car"
        else:
            vtype = vehicle_type

        prefix = "AMB" if vtype == "Ambulance" else ("BUS" if vtype == "Bus" else ("EV" if vtype == "EV Taxi" else ("AUTO" if vtype == "Auto Rickshaw" else "CAR")))
        vid = f"{prefix}-{self.vehicle_counter}"

        edge = self.network.edge_data.get(edge_key, {})
        speed_lim = edge.get("speed_limit", 13.88)
        init_speed = 0.0 if is_queued else min(speed_lim, float(np.random.uniform(9.0, 14.0)))

        veh = Vehicle(
            id=vid,
            vehicle_type=vtype,
            origin=edge_key[0],
            destination=edge_key[1],
            entry_time=self.time,
            current_edge=edge_key,
            edge_length=self.network.block_length,
            position_on_edge=progress * self.network.block_length,
            progress=progress,
            speed=init_speed,
            is_queued=is_queued,
            waiting_time=float(np.random.uniform(2.0, 15.0)) if is_queued else 0.0,
            status_label="Queued at Signal" if is_queued else ("🚨 Emergency En Route" if vtype == "Ambulance" else "Cruising"),
        )

        if veh.is_emergency:
            self.last_emergency_id = veh.id

        self.vehicles[veh.id] = veh
        return veh

    def _initialize_traffic(self):
        """Pre-populate network edges with realistic initial vehicles and queues."""
        self.vehicles.clear()
        for edge_key, data in self.network.edge_data.items():
            base_init = np.random.randint(4, 12)
            if self.scenario == "morning_peak" and data["direction"] in ("E", "W"):
                base_init = int(base_init * 1.8)
            elif self.scenario == "evening_peak" and data["direction"] in ("N", "S"):
                base_init = int(base_init * 1.8)
            elif self.scenario == "traffic_spike" and data["to"] == "A":
                base_init = int(base_init * 2.5)

            num_queued = min(data["capacity"] - 2, base_init)
            num_moving = np.random.randint(2, 6)

            data["queued_vehicles"] = num_queued
            data["moving_vehicles"] = num_moving
            data["avg_waiting_time"] = float(np.random.uniform(8.0, 25.0))

            # Populate tracked vehicle objects
            for i in range(num_queued):
                prog = 0.82 + (0.16 * (i / max(1, num_queued)))
                self._create_vehicle(edge_key, is_queued=True, progress=min(0.98, prog))

            for j in range(num_moving):
                prog = 0.10 + (0.65 * (j / max(1, num_moving)))
                self._create_vehicle(edge_key, is_queued=False, progress=prog)

        self._update_all_vehicle_coordinates()

    def set_scenario(self, scenario: str):
        if scenario in self.SCENARIOS:
            self.scenario = scenario

    def set_city(self, city_name: str):
        """Update active metropolitan city for GPS projections."""
        self.city_name = city_name
        self._update_all_vehicle_coordinates()

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

    def spawn_emergency_vehicle(self, origin: Optional[str] = None, destination: Optional[str] = None) -> Vehicle:
        """
        Manually or programmatically inject a priority emergency vehicle (Ambulance)
        to demonstrate real-time GPS tracking and emergency preemption.
        """
        ingress_edges = [k for k in self.network.edge_data.keys() if k[0].startswith("IN_")]
        edge_key = ingress_edges[0] if ingress_edges else list(self.network.edge_data.keys())[0]

        veh = self._create_vehicle(edge_key, is_queued=False, progress=0.05, vehicle_type="Ambulance")
        veh.origin = origin or edge_key[0]
        veh.destination = destination or edge_key[1]
        self.emergency_preemption_active = True
        self.last_emergency_id = veh.id
        self._update_vehicle_coordinates(veh)
        return veh

    def _update_vehicle_coordinates(self, veh: Vehicle):
        """Compute geographic GPS coordinates for a vehicle along its road edge."""
        if not isinstance(veh.current_edge, (tuple, list)) or len(veh.current_edge) < 2:
            return
        u, v = veh.current_edge[0], veh.current_edge[1]
        u_geo = get_city_node_geo(u, self.city_name)
        v_geo = get_city_node_geo(v, self.city_name)
        veh.update_gps(u_geo["lat"], u_geo["lon"], v_geo["lat"], v_geo["lon"])

    def _update_all_vehicle_coordinates(self):
        """Update GPS coordinates for all active tracked vehicles."""
        for veh in self.vehicles.values():
            self._update_vehicle_coordinates(veh)

    def step(self, signal_actions: Optional[Dict[str, Dict[str, float]]] = None) -> Dict[str, Any]:
        """
        Execute one discrete simulation step of dt seconds.
        Advances traffic signals, discrete vehicle kinematics, and queue dynamics.
        """
        if signal_actions:
            self.apply_signal_plan(signal_actions)

        # 1. Update all traffic signals
        for signal in self.network.signals.values():
            signal.update(self.dt)

        scenario_cfg = self.SCENARIOS.get(self.scenario, self.SCENARIOS["normal"])
        base_arrival = scenario_cfg.get("base_rate", 0.35)

        # 2. Ingress Vehicle Generation
        for (u, v), edge in self.network.edge_data.items():
            if u.startswith("IN_"):
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

                new_arrivals = int(np.random.poisson(rate * (self.dt / 2.0)))
                available_space = max(0, edge["capacity"] - (edge["queued_vehicles"] + edge["moving_vehicles"]))
                admitted = min(new_arrivals, available_space)

                for _ in range(admitted):
                    self._create_vehicle((u, v), is_queued=False, progress=0.02)

        # 3. Process discrete vehicle movement and queue dynamics
        to_remove = []
        has_emergency_approaching = False

        for vid, veh in list(self.vehicles.items()):
            u, v = veh.current_edge[0], veh.current_edge[1]
            edge = self.network.edge_data.get((u, v))
            if not edge:
                to_remove.append(vid)
                continue

            # Check downstream signal
            is_green = True
            if v in self.network.signals:
                signal = self.network.signals[v]
                is_green = signal.is_green_for_approach(edge["direction"])

            # Check if this vehicle is emergency
            if veh.is_emergency and not veh.has_arrived:
                if veh.progress > 0.5:
                    has_emergency_approaching = True

            # If vehicle is queued
            if veh.is_queued:
                veh.update_wait(self.dt)
                if is_green:
                    # Saturation discharge chance on green
                    discharge_prob = min(0.95, 0.55 * self.dt)
                    if random.random() < discharge_prob or veh.is_emergency:
                        # Released through intersection
                        veh.is_queued = False
                        veh.status_label = "Crossing on Green"
                        # Route through intersection v
                        outgoing = self.network.get_outgoing_edges(v)
                        if outgoing:
                            next_edge = random.choice(outgoing)
                            next_data = self.network.edge_data[next_edge]
                            if next_data["to"].startswith("OUT_"):
                                veh.has_arrived = True
                                self.completed_trips += 1
                                self.total_completed_wait += veh.waiting_time
                                to_remove.append(vid)
                            else:
                                veh.current_edge = next_edge
                                veh.progress = 0.05
                                veh.position_on_edge = 0.05 * self.network.block_length
                                veh.speed = float(np.random.uniform(8.0, 13.0))
                else:
                    veh.status_label = "Queued at Red Light"
            else:
                # Vehicle is moving
                veh.advance(self.dt, max_speed_mps=edge.get("speed_limit", 13.88))
                if veh.progress >= 0.88:
                    if is_green or (veh.is_emergency and veh.progress >= 0.96):
                        # Free flow through intersection
                        outgoing = self.network.get_outgoing_edges(v)
                        if outgoing:
                            next_edge = random.choice(outgoing)
                            next_data = self.network.edge_data[next_edge]
                            if next_data["to"].startswith("OUT_"):
                                veh.has_arrived = True
                                self.completed_trips += 1
                                self.total_completed_wait += veh.waiting_time
                                to_remove.append(vid)
                            else:
                                veh.current_edge = next_edge
                                veh.progress = 0.05
                                veh.position_on_edge = 0.05 * self.network.block_length
                        else:
                            veh.has_arrived = True
                            to_remove.append(vid)
                    else:
                        # Red light queue join
                        veh.is_queued = True
                        veh.speed = 0.0
                        veh.progress = min(0.98, max(0.88, veh.progress))
                        veh.status_label = "Queued at Red Light"

            # Update GPS coordinates
            self._update_vehicle_coordinates(veh)

        # Remove departed vehicles
        for vid in to_remove:
            if vid in self.vehicles:
                del self.vehicles[vid]

        # Keep fleet count bounded for high rendering performance (max ~120 vehicles)
        if len(self.vehicles) > 120:
            excess = len(self.vehicles) - 120
            non_emergency = [vid for vid, v in self.vehicles.items() if not v.is_emergency and v.progress > 0.7]
            for vid in non_emergency[:excess]:
                del self.vehicles[vid]

        self.emergency_preemption_active = has_emergency_approaching

        # 4. Synchronize aggregate edge metrics with vehicle counts
        for edge_key, data in self.network.edge_data.items():
            edge_vehs = [v for v in self.vehicles.values() if v.current_edge == edge_key]
            q_vehs = [v for v in edge_vehs if v.is_queued]
            m_vehs = [v for v in edge_vehs if not v.is_queued]

            data["queued_vehicles"] = len(q_vehs)
            data["moving_vehicles"] = len(m_vehs)
            if q_vehs:
                data["avg_waiting_time"] = float(np.mean([v.waiting_time for v in q_vehs]))
            else:
                data["avg_waiting_time"] = max(0.0, data["avg_waiting_time"] - self.dt * 0.5)

        # 5. Advance clock
        self.time += self.dt
        self.step_count += 1

        # 6. Harvest instantaneous state snapshot
        state = self.get_state()
        self.history.append(state)
        return state

    def get_fleet_summary(self) -> Dict[str, Any]:
        """Aggregate breakdown of tracked vehicles by category and kinematics."""
        type_counts = {"Car": 0, "Bus": 0, "Ambulance": 0, "EV Taxi": 0, "Auto Rickshaw": 0}
        moving_count = 0
        queued_count = 0
        speeds = []

        for veh in self.vehicles.values():
            type_counts[veh.vehicle_type] = type_counts.get(veh.vehicle_type, 0) + 1
            if veh.is_queued:
                queued_count += 1
            else:
                moving_count += 1
                speeds.append(veh.speed_kmh)

        avg_fleet_speed = float(np.mean(speeds)) if speeds else 38.0

        return {
            "total_tracked": len(self.vehicles),
            "moving_count": moving_count,
            "queued_count": queued_count,
            "avg_speed_kmh": round(avg_fleet_speed, 1),
            "by_type": type_counts,
            "emergency_active": self.emergency_preemption_active,
            "last_emergency_id": self.last_emergency_id,
        }

    def get_tracked_vehicles(self, city_name: Optional[str] = None, max_count: int = 80) -> List[Dict[str, Any]]:
        """
        Return serialized list of live vehicle dictionaries with GPS coordinates and telemetry.
        Prioritizes emergency vehicles, moving vehicles, and high-wait queues.
        """
        target_city = city_name or self.city_name
        veh_list = list(self.vehicles.values())

        # Sort so emergency vehicles and active movers appear first
        veh_list.sort(key=lambda v: (not v.is_emergency, v.is_queued, -v.speed), reverse=False)

        res = []
        for veh in veh_list[:max_count]:
            v_dict = veh.to_dict()
            res.append(v_dict)
        return res

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

        tracked_vehs = self.get_tracked_vehicles(city_name=self.city_name)
        fleet_sum = self.get_fleet_summary()

        return {
            "timestamp": round(self.time, 1),
            "step": self.step_count,
            "scenario": self.scenario,
            "city_name": self.city_name,
            "num_intersections": self.num_intersections,
            "total_vehicles": total_volume,
            "total_queued": total_queued,
            "global_avg_wait": round(global_avg_wait, 1),
            "global_congestion": round(global_congestion, 3),
            "throughput_veh_per_min": throughput,
            "intersections": intersection_stats,
            "tracked_vehicles": tracked_vehs,
            "fleet_summary": fleet_sum,
            "emergency_preemption_active": self.emergency_preemption_active,
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
        self.vehicles.clear()
        self._initialize_traffic()
