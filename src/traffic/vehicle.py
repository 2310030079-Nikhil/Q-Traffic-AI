"""
Vehicle representation and real-time GPS tracking for Q-TrafficAI simulator.
Supports multi-modal traffic: passenger cars, city transit buses, emergency ambulances,
EV taxis, and auto-rickshaws with discrete kinematics and coordinate interpolation.
"""

from dataclasses import dataclass, field
from typing import Tuple, List, Dict, Any, Optional
import uuid


VEHICLE_TYPE_CONFIG = {
    "Car": {
        "icon": "🚗",
        "color": "#00f2fe",
        "target_speed": 13.88,  # ~50 km/h
        "is_emergency": False,
        "priority_level": 1,
    },
    "Bus": {
        "icon": "🚌",
        "color": "#f59e0b",
        "target_speed": 10.0,  # ~36 km/h
        "is_emergency": False,
        "priority_level": 2,
    },
    "Ambulance": {
        "icon": "🚑",
        "color": "#ef4444",
        "target_speed": 18.0,  # ~65 km/h
        "is_emergency": True,
        "priority_level": 5,
    },
    "EV Taxi": {
        "icon": "🚖",
        "color": "#10b981",
        "target_speed": 13.0,  # ~47 km/h
        "is_emergency": False,
        "priority_level": 1,
    },
    "Auto Rickshaw": {
        "icon": "🛺",
        "color": "#eab308",
        "target_speed": 9.5,  # ~34 km/h
        "is_emergency": False,
        "priority_level": 1,
    },
}


@dataclass
class Vehicle:
    """
    Represents an individual vehicle tracked in real-time across the urban grid.
    """
    id: str = field(default_factory=lambda: f"VEH-{uuid.uuid4().hex[:5].upper()}")
    vehicle_type: str = "Car"
    origin: str = ""
    destination: str = ""
    entry_time: float = 0.0
    current_edge: Any = ("", "")
    position_on_edge: float = 0.0  # meters along edge
    edge_length: float = 300.0  # default block length in meters
    progress: float = 0.0  # 0.0 to 1.0 along current edge
    speed: float = 12.0  # m/s (~43 km/h)
    target_speed: float = 13.88  # 50 km/h
    waiting_time: float = 0.0
    is_queued: bool = False
    is_emergency: bool = False
    has_arrived: bool = False
    route_path: List[str] = field(default_factory=list)
    route_index: int = 0
    color: str = "#00f2fe"
    icon: str = "🚗"
    lat: float = 0.0
    lon: float = 0.0
    status_label: str = "Cruising"

    def __post_init__(self):
        cfg = VEHICLE_TYPE_CONFIG.get(self.vehicle_type, VEHICLE_TYPE_CONFIG["Car"])
        if not self.icon or self.icon == "🚗":
            self.icon = cfg["icon"]
        if not self.color or self.color == "#00f2fe":
            self.color = cfg["color"]
        if self.target_speed == 13.88 and self.vehicle_type != "Car":
            self.target_speed = cfg["target_speed"]
        self.is_emergency = cfg["is_emergency"]
        if self.is_emergency:
            self.status_label = "🚨 Emergency Siren Active"

    def update_wait(self, dt: float):
        """Update waiting time when vehicle is stopped in queue."""
        if self.is_queued:
            self.waiting_time += dt

    @property
    def speed_kmh(self) -> float:
        """Vehicle current speed in km/h."""
        return round(self.speed * 3.6, 1)

    def advance(self, dt: float, max_speed_mps: float = 15.0) -> float:
        """
        Advance vehicle along current edge based on kinematics.
        Returns distance moved in meters.
        """
        if self.is_queued or self.has_arrived:
            self.speed = 0.0
            return 0.0

        # Emergency vehicles cruise faster and overtake queue when possible
        effective_target = self.target_speed * (1.3 if self.is_emergency else 1.0)
        clamped_target = min(effective_target, max_speed_mps)

        # Smooth acceleration / deceleration toward target speed
        accel = 2.5 if self.is_emergency else 1.8
        if self.speed < clamped_target:
            self.speed = min(clamped_target, self.speed + accel * dt)
        elif self.speed > clamped_target:
            self.speed = max(clamped_target, self.speed - 2.5 * dt)

        dist = self.speed * dt
        self.position_on_edge += dist
        self.progress = min(1.0, max(0.0, self.position_on_edge / max(1.0, self.edge_length)))
        self.status_label = "Cruising" if not self.is_emergency else "🚨 Emergency En Route"
        return dist

    def update_gps(self, u_lat: float, u_lon: float, v_lat: float, v_lon: float):
        """
        Interpolate geographic coordinates based on progress along road link (u, v).
        """
        p = max(0.0, min(1.0, self.progress))
        self.lat = u_lat + p * (v_lat - u_lat)
        self.lon = u_lon + p * (v_lon - u_lon)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize vehicle state for real-time telemetry APIs and UI tables."""
        edge_str = f"{self.current_edge[0]} ➔ {self.current_edge[1]}" if isinstance(self.current_edge, (tuple, list)) and len(self.current_edge) == 2 else str(self.current_edge)
        return {
            "id": self.id,
            "type": self.vehicle_type,
            "icon": self.icon,
            "color": self.color,
            "edge": edge_str,
            "from_node": self.current_edge[0] if isinstance(self.current_edge, (tuple, list)) else "",
            "to_node": self.current_edge[1] if isinstance(self.current_edge, (tuple, list)) else "",
            "progress_pct": round(self.progress * 100, 1),
            "speed_kmh": self.speed_kmh,
            "waiting_time_s": round(self.waiting_time, 1),
            "is_queued": self.is_queued,
            "is_emergency": self.is_emergency,
            "status": self.status_label,
            "lat": round(self.lat, 6),
            "lon": round(self.lon, 6),
            "origin": self.origin,
            "destination": self.destination,
        }
