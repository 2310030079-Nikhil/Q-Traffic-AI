"""
Road network graph and topology generator for 4, 6, and 9 intersections.
"""

from typing import Dict, List, Tuple, Any
import networkx as nx
from src.traffic.signal import TrafficSignal


class TrafficNetwork:
    """
    Manages grid network topology with intersections, road links, and signal controllers.
    """

    def __init__(self, num_intersections: int = 4, block_length: float = 300.0):
        self.num_intersections = num_intersections
        self.block_length = block_length
        self.graph = nx.DiGraph()
        self.signals: Dict[str, TrafficSignal] = {}
        self.node_positions: Dict[str, Tuple[float, float]] = {}
        self.edge_data: Dict[Tuple[str, str], Dict[str, Any]] = {}

        self._build_topology()

    def _build_topology(self):
        """Construct a 2x2 (4 nodes), 2x3 (6 nodes), or 3x3 (9 nodes) grid network."""
        if self.num_intersections == 4:
            rows, cols = 2, 2
        elif self.num_intersections == 6:
            rows, cols = 2, 3
        elif self.num_intersections == 9:
            rows, cols = 3, 3
        else:
            rows, cols = 2, 2

        # Create intersection nodes with positions and signals
        idx = 0
        node_grid = []
        for r in range(rows):
            row_nodes = []
            for c in range(cols):
                node_id = chr(65 + idx)  # 'A', 'B', 'C', ...
                row_nodes.append(node_id)
                pos = (c * self.block_length, (rows - 1 - r) * self.block_length)
                self.node_positions[node_id] = pos
                self.signals[node_id] = TrafficSignal(intersection_id=node_id)
                self.graph.add_node(node_id, pos=pos, signal=self.signals[node_id])
                idx += 1
            node_grid.append(row_nodes)

        # Internal bidirectional connections between grid neighbors
        for r in range(rows):
            for c in range(cols):
                curr = node_grid[r][c]
                # Horizontal neighbor (East)
                if c + 1 < cols:
                    east = node_grid[r][c + 1]
                    self._add_road_pair(curr, east, "E", "W")
                # Vertical neighbor (South)
                if r + 1 < rows:
                    south = node_grid[r + 1][c]
                    self._add_road_pair(curr, south, "S", "N")

        # Boundary ingress and egress dummy nodes for incoming & outgoing city traffic
        for r in range(rows):
            for c in range(cols):
                curr = node_grid[r][c]
                pos = self.node_positions[curr]

                # North ingress/egress if on top row
                if r == 0:
                    n_in = f"IN_N_{curr}"
                    n_out = f"OUT_N_{curr}"
                    self.node_positions[n_in] = (pos[0], pos[1] + self.block_length)
                    self.node_positions[n_out] = (pos[0], pos[1] + self.block_length)
                    self._add_road(n_in, curr, direction="S", capacity=40)
                    self._add_road(curr, n_out, direction="N", capacity=40)

                # South ingress/egress if on bottom row
                if r == rows - 1:
                    s_in = f"IN_S_{curr}"
                    s_out = f"OUT_S_{curr}"
                    self.node_positions[s_in] = (pos[0], pos[1] - self.block_length)
                    self.node_positions[s_out] = (pos[0], pos[1] - self.block_length)
                    self._add_road(s_in, curr, direction="N", capacity=40)
                    self._add_road(curr, s_out, direction="S", capacity=40)

                # West ingress/egress if on left column
                if c == 0:
                    w_in = f"IN_W_{curr}"
                    w_out = f"OUT_W_{curr}"
                    self.node_positions[w_in] = (pos[0] - self.block_length, pos[1])
                    self.node_positions[w_out] = (pos[0] - self.block_length, pos[1])
                    self._add_road(w_in, curr, direction="E", capacity=40)
                    self._add_road(curr, w_out, direction="W", capacity=40)

                # East ingress/egress if on right column
                if c == cols - 1:
                    e_in = f"IN_E_{curr}"
                    e_out = f"OUT_E_{curr}"
                    self.node_positions[e_in] = (pos[0] + self.block_length, pos[1])
                    self.node_positions[e_out] = (pos[0] + self.block_length, pos[1])
                    self._add_road(e_in, curr, direction="W", capacity=40)
                    self._add_road(curr, e_out, direction="E", capacity=40)

    def _add_road(self, u: str, v: str, direction: str, capacity: int = 35):
        """Add single directional road."""
        self.graph.add_edge(u, v)
        self.edge_data[(u, v)] = {
            "from": u,
            "to": v,
            "length": self.block_length,
            "speed_limit": 13.88,  # 50 km/h in m/s
            "capacity": capacity,
            "direction": direction,  # Direction approaching target node v
            "queued_vehicles": 0,
            "moving_vehicles": 0,
            "avg_waiting_time": 0.0,
            "avg_speed": 12.0,
        }

    def _add_road_pair(self, u: str, v: str, dir_uv: str, dir_vu: str):
        """Add bidirectional road pair between internal intersections."""
        self._add_road(u, v, direction=dir_uv, capacity=40)
        self._add_road(v, u, direction=dir_vu, capacity=40)

    def get_intersection_ids(self) -> List[str]:
        return list(self.signals.keys())

    def get_incoming_edges(self, intersection_id: str) -> List[Tuple[str, str]]:
        return [(u, v) for u, v in self.graph.in_edges(intersection_id)]

    def get_outgoing_edges(self, intersection_id: str) -> List[Tuple[str, str]]:
        return [(u, v) for u, v in self.graph.out_edges(intersection_id)]
