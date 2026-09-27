"""
Vehicle representation and tracking for Q-TrafficAI simulator.
"""

from dataclasses import dataclass, field
import uuid


@dataclass
class Vehicle:
    id: str = field(default_factory=lambda: f"veh_{uuid.uuid4().hex[:6]}")
    origin: str = ""
    destination: str = ""
    entry_time: float = 0.0
    current_edge: str = ""
    position_on_edge: float = 0.0  # meters along edge
    speed: float = 12.0  # m/s (~43 km/h)
    target_speed: float = 13.88  # 50 km/h
    waiting_time: float = 0.0
    is_queued: bool = False
    has_arrived: bool = False

    def update_wait(self, dt: float):
        if self.is_queued:
            self.waiting_time += dt
