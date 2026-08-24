"""Sensor system for agent perception via raycasting."""

import math
import numpy as np
from models import Agent, Bullet
from config import *
from core.heatmap import Mapdata

def cast_ray_obstacle(agent: Agent, dir_x: float, dir_y: float, obstacles: list) -> float:
    """Returns the closest ray-circle intersection distance among obstacles, or RAY_MAX_DIST."""
    closest = RAY_MAX_DIST
    for obs in obstacles:
        dx = obs.x - agent.x
        dy = obs.y - agent.y
        projection = dx * dir_x + dy * dir_y
        if projection <= 0:
            continue
        perp_dist_sq = (dx * dx + dy * dy) - (projection * projection)
        r_sq = obs.r * obs.r
        if perp_dist_sq <= r_sq:
            dist = projection - math.sqrt(max(0.0, r_sq - perp_dist_sq))
            if 0 < dist < closest:
                closest = dist
    return closest


def cast_ray(agent: Agent,ray_angle: float,target_agents: list[Agent],bullets: list[Bullet],obstacles: list,) -> tuple[float, float, float, float]:
    """Casts a ray and returns normalized distances to (Wall/Obstacle, Enemy, Teammate, Enemy Bullet)."""
    dir_x = math.cos(agent.angle + ray_angle)
    dir_y = math.sin(agent.angle + ray_angle)

    # 1. Wall Distance
    wall_dist = RAY_MAX_DIST
    if dir_x > 0:
        wall_dist = min(wall_dist, (ARENA_W - agent.x) / dir_x)
    elif dir_x < 0:
        wall_dist = min(wall_dist, -agent.x / dir_x)
    if dir_y > 0:
        wall_dist = min(wall_dist, (ARENA_H - agent.y) / dir_y)
    elif dir_y < 0:
        wall_dist = min(wall_dist, -agent.y / dir_y)

    # 1b. Obstacles block sight the same as walls do
    wall_dist = min(wall_dist, cast_ray_obstacle(agent, dir_x, dir_y, obstacles))

    # 2. Agent Intersections along Ray
    enemy_dist = RAY_MAX_DIST
    mate_dist = RAY_MAX_DIST

    for other in target_agents:
        if not other.alive or other is agent:
            continue

        dx = other.x - agent.x
        dy = other.y - agent.y
        projection = dx * dir_x + dy * dir_y

        if projection > 0:
            perp_dist_sq = (dx * dx + dy * dy) - (projection * projection)
            if perp_dist_sq <= AGENT_RADIUS * AGENT_RADIUS:
                dist = projection - math.sqrt(max(0.0, AGENT_RADIUS * AGENT_RADIUS - perp_dist_sq))
                if dist < RAY_MAX_DIST:
                    if other.team != agent.team:
                        enemy_dist = min(enemy_dist, dist)
                    else:
                        mate_dist = min(mate_dist, dist)

    # 3. Incoming Enemy Bullet Intersections along Ray
    bullet_dist = RAY_MAX_DIST
    for b in bullets:
        if b.team == agent.team:
            continue

        p0_x, p0_y = b.x - b.vx, b.y - b.vy
        p1_x, p1_y = b.x, b.y

        x1, y1 = p0_x - agent.x, p0_y - agent.y
        x2, y2 = p1_x - agent.x, p1_y - agent.y

        rx, ry = dir_x, dir_y

        denom = rx * (y2 - y1) - ry * (x2 - x1)
        if abs(denom) > 1e-6:
            t = (x1 * (y2 - y1) - y1 * (x2 - x1)) / denom
            u = (x1 * ry - y1 * rx) / denom

            if 0 <= t < bullet_dist and 0.0 <= u <= 1.0:
                bullet_dist = t

    return (
        min(1.0, wall_dist / RAY_MAX_DIST),
        min(1.0, enemy_dist / RAY_MAX_DIST),
        min(1.0, mate_dist / RAY_MAX_DIST),
        min(1.0, bullet_dist / RAY_MAX_DIST),
    )


def compute_sensors(agent: Agent, all_agents: list[Agent], bullets: list[Bullet], obstacles: list) -> np.ndarray:
    wall_inputs = []
    enemy_inputs = []
    mate_inputs = []
    bullet_inputs = []

    for rel_angle in RAY_ANGLES:
        w_d, e_d, m_d, b_d = cast_ray(agent, rel_angle, all_agents, bullets, obstacles)
        wall_inputs.append(w_d)
        enemy_inputs.append(e_d)
        mate_inputs.append(m_d)
        bullet_inputs.append(b_d)

    health_pct = agent.health / AGENT_MAX_HEALTH
    cooldown_ready = 1.0 - (agent.cooldown / AGENT_MAX_COOLDOWN)
    boost_pct = agent.boost_fuel / BOOSTER_MAX_FUEL

    return np.array(
        wall_inputs + enemy_inputs + mate_inputs + bullet_inputs +
        [health_pct, cooldown_ready, boost_pct, 1.0],
        dtype=np.float64,
    )

# -------------------------------------------------------------------------
# MAP DATA Routines

def cast_ray_obstacle_md(agent: Agent, dir_x: float, dir_y: float, obstacles: list) -> float:
    """Returns the closest ray-circle intersection distance among obstacles, or RAY_MAX_DIST."""
    closest = RAY_MAX_DIST
    for obs in obstacles:
        dx = obs.x - agent.x
        dy = obs.y - agent.y
        projection = dx * dir_x + dy * dir_y
        if projection <= 0:
            continue
        perp_dist_sq = (dx * dx + dy * dy) - (projection * projection)
        r_sq = obs.r * obs.r
        if perp_dist_sq <= r_sq:
            dist = projection - math.sqrt(max(0.0, r_sq - perp_dist_sq))
            if 0 < dist < closest:
                closest = dist
    return closest


def cast_ray_md(agent: Agent,ray_angle: float,target_agents: list[Agent],bullets: list[Bullet],obstacles: list,) -> tuple[float, float, float, float]:
    """Casts a ray and returns normalized distances to (Wall/Obstacle, Enemy, Teammate, Enemy Bullet)."""
    dir_x = math.cos(agent.angle + ray_angle)
    dir_y = math.sin(agent.angle + ray_angle)

    wall_dist = RAY_MAX_DIST
    if dir_x > 0:
        wall_dist = min(wall_dist, (ARENA_W - agent.x) / dir_x)
    elif dir_x < 0:
        wall_dist = min(wall_dist, -agent.x / dir_x)
    if dir_y > 0:
        wall_dist = min(wall_dist, (ARENA_H - agent.y) / dir_y)
    elif dir_y < 0:
        wall_dist = min(wall_dist, -agent.y / dir_y)

    wall_dist = min(wall_dist, cast_ray_obstacle(agent, dir_x, dir_y, obstacles))

    enemy_dist = RAY_MAX_DIST
    mate_dist = RAY_MAX_DIST

    for other in target_agents:
        if not other.alive or other is agent:
            continue

        dx = other.x - agent.x
        dy = other.y - agent.y
        projection = dx * dir_x + dy * dir_y

        if projection > 0:
            perp_dist_sq = (dx * dx + dy * dy) - (projection * projection)
            if perp_dist_sq <= AGENT_RADIUS * AGENT_RADIUS:
                dist = projection - math.sqrt(max(0.0, AGENT_RADIUS * AGENT_RADIUS - perp_dist_sq))
                if dist < RAY_MAX_DIST:
                    if other.team != agent.team:
                        enemy_dist = min(enemy_dist, dist)
                    else:
                        mate_dist = min(mate_dist, dist)

    bullet_dist = RAY_MAX_DIST
    for b in bullets:
        if b.team == agent.team:
            continue

        p0_x, p0_y = b.x - b.vx, b.y - b.vy
        p1_x, p1_y = b.x, b.y

        x1, y1 = p0_x - agent.x, p0_y - agent.y
        x2, y2 = p1_x - agent.x, p1_y - agent.y

        rx, ry = dir_x, dir_y

        denom = rx * (y2 - y1) - ry * (x2 - x1)
        if abs(denom) > 1e-6:
            t = (x1 * (y2 - y1) - y1 * (x2 - x1)) / denom
            u = (x1 * ry - y1 * rx) / denom

            if 0 <= t < bullet_dist and 0.0 <= u <= 1.0:
                bullet_dist = t

    return (
        min(1.0, wall_dist / RAY_MAX_DIST),
        min(1.0, enemy_dist / RAY_MAX_DIST),
        min(1.0, mate_dist / RAY_MAX_DIST),
        min(1.0, bullet_dist / RAY_MAX_DIST),
    )

def compute_sensors_md(agent: Agent,all_agents: list[Agent],bullets: list[Bullet],obstacles: list,heatmap: Mapdata) -> np.ndarray:
    wall_inputs = []
    enemy_inputs = []
    mate_inputs = []
    bullet_inputs = []
    death_inputs = []  # new

    for rel_angle in RAY_ANGLES:
        w_d, e_d, m_d, b_d = cast_ray(agent, rel_angle, all_agents, bullets, obstacles)
        d_d = heatmap_cast_ray(agent, rel_angle, heatmap)  # new

        wall_inputs.append(w_d)
        enemy_inputs.append(e_d)
        mate_inputs.append(m_d)
        bullet_inputs.append(b_d)
        death_inputs.append(d_d)

    health_pct = agent.health / AGENT_MAX_HEALTH
    cooldown_ready = 1.0 - (agent.cooldown / AGENT_MAX_COOLDOWN)
    boost_pct = agent.boost_fuel / BOOSTER_MAX_FUEL

    # Now 40 sensor inputs + 3 stats + bias = 44
    return np.array(
        wall_inputs + enemy_inputs + mate_inputs + bullet_inputs + death_inputs +
        [health_pct, cooldown_ready, boost_pct, 1.0],
        dtype=np.float64,
    )
