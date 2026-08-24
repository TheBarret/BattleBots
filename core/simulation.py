"""Main simulation orchestration."""

import math
import numpy as np
from models import Agent, Bullet
from core.world import World
from core.physics import resolve_obstacle_collision, bullet_hits_obstacle, obstacle_edge_distance
from core.sensors import compute_sensors
from audio import SoundBits
from config import *


class Simulation:
    """Orchestrates a single simulation tick."""

    def __init__(self, world: World, audio: SoundBits):
        self.world = world
        self.audio = audio
        self.agents: list[Agent] = []
        self.bullets: list[Bullet] = []
        self.frame = 0

    def reset(self, team_nets: list[list]) -> None:
        """Reset simulation with new population."""
        self.agents = self.world.spawn_agents(team_nets)
        self.bullets = []
        self.frame = 0

    def step(self) -> None:
        """Advance simulation by one frame."""
        self.frame += 1
        self.audio.begin_frame()

        # 1) Think & Act
        for agent in self.agents:
            if not agent.alive:
                continue
            agent.survival_frames += 1
            if agent.cooldown > 0:
                agent.cooldown -= 1

            # Proximity Reward & Wall Penalties
            enemies = [o for o in self.agents if o.team != agent.team and o.alive]
            if enemies:
                closest_enemy_dist = min(math.hypot(o.x - agent.x, o.y - agent.y) for o in enemies)
                agent.proximity_reward += max(0.0, (ARENA_W - closest_enemy_dist) / ARENA_W)

            wall_dist = min(agent.x, ARENA_W - agent.x, agent.y, ARENA_H - agent.y)
            if wall_dist < 30.0:
                agent.wall_penalties += (30.0 - wall_dist) / 30.0

            # Obstacles penalize hugging the same way walls do
            obs_dist = obstacle_edge_distance(agent.x, agent.y, self.world.obstacles)
            if obs_dist < OBSTACLE_PENALTY_RADIUS:
                agent.wall_penalties += (OBSTACLE_PENALTY_RADIUS - obs_dist) / OBSTACLE_PENALTY_RADIUS

            # obtain sensor data
            sensors = compute_sensors(agent, self.agents, self.bullets, self.world.obstacles)

            # decide based on network data
            out = agent.net.forward(sensors)
            move = float(np.clip(out[0], -1.0, 1.0))
            turn = float(np.clip(out[1], -1.0, 1.0))
            shoot = out[2] > AGENT_FIRE_THR
            boost = out[3] > AGENT_BOOST_THR

            # Penalize turning when forward velocity is zero or very low
            if abs(turn) > FITNESS_LOW_T and abs(move) < FITNESS_LOW_M:
                agent.turn_penalties += abs(turn) * FITNESS_TR

            # Dual-use?
            if not AGENT_DUAL_USE and shoot and boost:
                boost = False

            # Handle Boost Fuel Tank
            speed = AGENT_SPEED
            agent.is_boosting = False

            if boost and agent.boost_fuel > 1.0:
                agent.is_boosting = True
                agent.boost_fuel = max(0.0, agent.boost_fuel - BOOSTER_DRAIN_RATE)
                speed *= (BOOSTER_SPEED_MULT + out[3])
            else:
                agent.boost_fuel = min(BOOSTER_MAX_FUEL, agent.boost_fuel + BOOSTER_RECHARGE_RATE)

            # Apply Movement with current dynamic speed
            agent.angle += turn * AGENT_TURN_RATE
            agent.x += math.cos(agent.angle) * move * speed
            agent.y += math.sin(agent.angle) * move * speed

            # Obstacles are solid: push the agent back out if movement drove it inside one.
            resolve_obstacle_collision(agent, self.world.obstacles)

            if shoot and agent.cooldown == 0:
                vx = math.cos(agent.angle) * BULLET_SPEED
                vy = math.sin(agent.angle) * BULLET_SPEED
                start_x = agent.x + math.cos(agent.angle) * BULLET_SPAWN_AT
                start_y = agent.y + math.sin(agent.angle) * BULLET_SPAWN_AT
                self.bullets.append(Bullet(start_x, start_y, vx, vy, agent.team, agent))
                agent.cooldown = AGENT_MAX_COOLDOWN
                agent.shots_fired += 1
                self.audio.play_fire(agent.team)

        # 2) Bullets lifecycle
        alive_bullets: list[Bullet] = []
        for b in self.bullets:
            b.x += b.vx
            b.y += b.vy
            b.life -= 1
            if b.life <= 0 or not (0 <= b.x <= ARENA_W and 0 <= b.y <= ARENA_H):
                continue
            if bullet_hits_obstacle(b, self.world.obstacles):
                continue
            alive_bullets.append(b)
        self.bullets = alive_bullets

        # 3) Bullet collisions
        surviving_bullets: list[Bullet] = []
        for b in self.bullets:
            hit = False
            for agent in self.agents:
                if not agent.alive:
                    continue

                dist = math.hypot(agent.x - b.x, agent.y - b.y)
                if dist <= BULLET_HIT_RADIUS:
                    if agent.team == b.team:
                        b.owner.bob_penalties += 1
                        agent.take_damage(BULLET_DAMAGE * 0.3)
                        hit = True
                        self.audio.play_hit()
                        break
                    else:
                        was_alive = agent.alive
                        agent.take_damage(BULLET_DAMAGE)
                        b.owner.damage_dealt += BULLET_DAMAGE
                        b.owner.hits_landed += 1
                        if was_alive and not agent.alive:
                            b.owner.kills += 1
                        hit = True
                        self.audio.play_hit()
                        break

            if not hit:
                surviving_bullets.append(b)

        self.bullets = surviving_bullets

    def team_alive_count(self, team: int) -> int:
        return sum(1 for a in self.agents if a.team == team and a.alive)

    def generation_over(self) -> bool:
        if self.frame >= FRAMES_PER_GEN:
            return True
        return self.team_alive_count(0) == 0 or self.team_alive_count(1) == 0
