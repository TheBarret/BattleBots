from __future__ import annotations
from config import *

# Obstacles
class Obstacle:
    __slots__ = ("x", "y", "r")

    def __init__(self, x: float, y: float, r: float):
        self.x = x
        self.y = y
        self.r = r


# Agent
class Agent:
    __slots__ = (
            "x", "y", "angle", "health", "cooldown", "alive",
            "team", "pop_idx", "net", "damage_dealt", "survival_frames",
            "shots_fired", "hits_landed", "kills", "wall_penalties", "proximity_reward", "bob_penalties",
            "boost_fuel", "is_boosting", "turn_penalties",
        )

    def __init__(self, x: float, y: float, angle: float, team: int, pop_idx: int, net: Network):
        self.team = team
        self.pop_idx = pop_idx
        self.net = net
        self.reset(x, y, angle)

    def reset(self, x: float, y: float, angle: float) -> None:
        self.x = x
        self.y = y
        self.angle = angle
        self.health = AGENT_MAX_HEALTH
        self.cooldown = 0
        self.alive = True
        self.damage_dealt = 0.0
        self.survival_frames = 0
        self.shots_fired = 0
        self.hits_landed = 0
        self.kills = 0
        self.wall_penalties = 0.0
        self.proximity_reward = 0.0
        self.bob_penalties = 0.0
        self.boost_fuel = BOOSTER_MAX_FUEL
        self.is_boosting = False
        self.turn_penalties = 0.0

    def fitness(self) -> float:
        # Aggressive combat-focused fitness function
        misses = self.shots_fired - self.hits_landed
        fit = (
            (self.damage_dealt * FITNESS_DMGD) +               # High reward for hitting enemies
            (self.kills * FITNESS_KILL) +                      # Flat bonus for finishing a kill
            (self.shots_fired * FITNESS_FIGHTER) +             # Flat bonus for activity
            (self.proximity_reward * FITNESS_PROX) -          # Reward closing distance to enemies
            (self.wall_penalties * FITNESS_WALL) -             # Penalty for hugging walls
            (misses * FITNESS_SHTF) -                             # Cost only for shots that missed
            (self.bob_penalties * FITNESS_BOB) -             # blue on blue
            (self.turn_penalties * FITNESS_TR)              # forever-rotate penalty
        )
        return max(0.0, fit)

    def take_damage(self, amount: float) -> None:
        if not self.alive:
            return
        self.health -= amount
        if self.health <= 0.0:
            self.health = 0.0
            self.alive = False

# Bullet
class Bullet:
    __slots__ = ("x", "y", "vx", "vy", "team", "owner", "life")

    def __init__(self, x: float, y: float, vx: float, vy: float, team: int, owner: Agent):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.team = team
        self.owner = owner
        self.life = BULLET_LIFETIME
