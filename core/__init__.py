"""Core simulation engine package."""

from core.physics import (
    resolve_obstacle_collision,
    bullet_hits_obstacle,
    obstacle_edge_distance,
    generate_obstacles,
)
from core.sensors import compute_sensors, cast_ray
from core.world import World
from core.simulation import Simulation

__all__ = [
    # Physics
    "resolve_obstacle_collision",
    "bullet_hits_obstacle",
    "obstacle_edge_distance",
    "generate_obstacles",
    # Sensors
    "compute_sensors",
    "cast_ray",
    # World & Simulation
    "World",
    "Simulation",
    "Mapdata"
]
