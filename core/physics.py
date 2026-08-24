"""Physics engine for movement, collision, and obstacle interactions."""

import math
import random
import numpy as np
from models import Agent, Bullet, Obstacle
from config import *


def _rect_circle_overlap(rect: tuple[float, float, float, float], cx: float, cy: float, cr: float) -> bool:
    x_min, x_max, y_min, y_max = rect
    nearest_x = max(x_min, min(cx, x_max))
    nearest_y = max(y_min, min(cy, y_max))
    return math.hypot(cx - nearest_x, cy - nearest_y) < cr


def generate_obstacles() -> list[Obstacle]:
    """Randomly places circular obstacles, keeping clear of spawn zones and each other."""
    clearance = OBSTACLE_SPAWN_CLEARANCE
    expanded_zones = [
        (x_min - clearance, x_max + clearance, y_min - clearance, y_max + clearance)
        for (x_min, x_max, y_min, y_max) in SPAWN_ZONES
    ]

    obstacles: list[Obstacle] = []
    for _ in range(OBSTACLE_COUNT):
        for _attempt in range(OBSTACLE_PLACEMENT_ATTEMPTS):
            r = random.uniform(OBSTACLE_MIN_RADIUS, OBSTACLE_MAX_RADIUS)
            x = random.uniform(r, ARENA_W - r)
            y = random.uniform(r, ARENA_H - r)

            if any(_rect_circle_overlap(z, x, y, r) for z in expanded_zones):
                continue
            if any(math.hypot(x - o.x, y - o.y) < (r + o.r + OBSTACLE_MIN_GAP) for o in obstacles):
                continue

            obstacles.append(Obstacle(x, y, r))
            break

    return obstacles


def resolve_obstacle_collision(agent: Agent, obstacles: list[Obstacle]) -> None:
    """Pushes an agent out of any obstacle it's overlapping (solid cover)."""
    for obs in obstacles:
        dx = agent.x - obs.x
        dy = agent.y - obs.y
        dist = math.hypot(dx, dy)
        min_dist = AGENT_RADIUS + obs.r
        if dist < min_dist:
            if dist == 0:
                dx, dy, dist = random.uniform(-1, 1), random.uniform(-1, 1), 0.001
            nx, ny = dx / dist, dy / dist
            overlap = min_dist - dist
            agent.x += nx * overlap
            agent.y += ny * overlap
    agent.x = float(np.clip(agent.x, AGENT_RADIUS, ARENA_W - AGENT_RADIUS))
    agent.y = float(np.clip(agent.y, AGENT_RADIUS, ARENA_H - AGENT_RADIUS))


def obstacle_edge_distance(x: float, y: float, obstacles: list[Obstacle]) -> float:
    """Distance from a point to the nearest obstacle's surface (RAY_MAX_DIST if none)."""
    closest = RAY_MAX_DIST
    for obs in obstacles:
        d = math.hypot(x - obs.x, y - obs.y) - obs.r
        if d < closest:
            closest = d
    return closest


def bullet_hits_obstacle(b: Bullet, obstacles: list[Obstacle]) -> bool:
    for obs in obstacles:
        if math.hypot(b.x - obs.x, b.y - obs.y) <= obs.r + BULLET_RADIUS:
            return True
    return False
