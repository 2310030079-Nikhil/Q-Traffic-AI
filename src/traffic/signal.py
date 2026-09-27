"""
Signal phase and controller logic for traffic intersections.
"""

from enum import IntEnum
from typing import Dict, Any


class SignalPhase(IntEnum):
    NS_GREEN = 0  # North-South Green, East-West Red
    NS_YELLOW = 1 # Transition
    EW_GREEN = 2  # East-West Green, North-South Red
    EW_YELLOW = 3 # Transition


class TrafficSignal:
    """
    Traffic signal controller representing a 2-stage (NS and EW) intersection.
    """

    def __init__(
        self,
        intersection_id: str,
        cycle_length: float = 60.0,
        green_ns: float = 27.0,
        green_ew: float = 27.0,
        yellow_duration: float = 3.0,
        min_green: float = 10.0,
        max_green: float = 50.0,
    ):
        self.intersection_id = intersection_id
        self.cycle_length = cycle_length
        self.green_ns = green_ns
        self.green_ew = green_ew
        self.yellow_duration = yellow_duration
        self.min_green = min_green
        self.max_green = max_green

        self.current_phase = SignalPhase.NS_GREEN
        self.time_in_phase = 0.0
        self.cycle_timer = 0.0

    def set_durations(self, green_ns: float, green_ew: float):
        """Update green phase durations dynamically from optimization plan."""
        # Enforce boundary constraints
        clamped_ns = max(self.min_green, min(self.max_green, green_ns))
        clamped_ew = max(self.min_green, min(self.max_green, green_ew))
        self.green_ns = clamped_ns
        self.green_ew = clamped_ew
        self.cycle_length = clamped_ns + clamped_ew + 2 * self.yellow_duration

    def update(self, dt: float) -> SignalPhase:
        """Advance signal timer by dt seconds and transition phases accordingly."""
        self.time_in_phase += dt
        self.cycle_timer = (self.cycle_timer + dt) % self.cycle_length

        if self.current_phase == SignalPhase.NS_GREEN:
            if self.time_in_phase >= self.green_ns:
                self.current_phase = SignalPhase.NS_YELLOW
                self.time_in_phase = 0.0
        elif self.current_phase == SignalPhase.NS_YELLOW:
            if self.time_in_phase >= self.yellow_duration:
                self.current_phase = SignalPhase.EW_GREEN
                self.time_in_phase = 0.0
        elif self.current_phase == SignalPhase.EW_GREEN:
            if self.time_in_phase >= self.green_ew:
                self.current_phase = SignalPhase.EW_YELLOW
                self.time_in_phase = 0.0
        elif self.current_phase == SignalPhase.EW_YELLOW:
            if self.time_in_phase >= self.yellow_duration:
                self.current_phase = SignalPhase.NS_GREEN
                self.time_in_phase = 0.0

        return self.current_phase

    def is_green_for_approach(self, approach_direction: str) -> bool:
        """
        Check if the light is currently green for a given incoming direction.
        Directions: 'N', 'S' -> NS_GREEN
                    'E', 'W' -> EW_GREEN
        """
        if approach_direction in ("N", "S"):
            return self.current_phase == SignalPhase.NS_GREEN
        elif approach_direction in ("E", "W"):
            return self.current_phase == SignalPhase.EW_GREEN
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intersection_id": self.intersection_id,
            "current_phase": self.current_phase.name,
            "time_in_phase": round(self.time_in_phase, 1),
            "green_ns": round(self.green_ns, 1),
            "green_ew": round(self.green_ew, 1),
            "cycle_length": round(self.cycle_length, 1),
        }
