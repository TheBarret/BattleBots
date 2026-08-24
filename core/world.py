"""World state management, spawning, and arena rules."""

import math
import random
from models import Agent, Obstacle
from core.physics import generate_obstacles
from config import *


class World:
    """Manages the arena state, spawns, and global world properties."""

    def __init__(self):
        self.obstacles: list[Obstacle] = generate_obstacles()
        self.generation = 1

    def spawn_agents(self, team_nets: list[list]) -> list[Agent]:
        """Spawn a new generation of agents from networks."""
        agents = []
        for team in range(2):
            for pop_idx, net in enumerate(team_nets[team]):
                x, y, angle = self._spawn_point(team)
                agents.append(Agent(x, y, angle, team, pop_idx, net))
        return agents

    def _spawn_point(self, team: int) -> tuple[float, float, float]:
        """Get spawn position for a team."""
        x_min, x_max, y_min, y_max = SPAWN_ZONES[team]
        x = random.uniform(x_min, x_max)
        y = random.uniform(y_min, y_max)
        angle = 0.0 if team == 0 else math.pi
        return x, y, angle

    def regenerate_obstacles(self) -> None:
        """Regenerate obstacle layout."""
        self.obstacles = generate_obstacles()
