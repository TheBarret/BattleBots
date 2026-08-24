import math
import pygame
from config import *
from models import Agent, Bullet


def agent_wireframe_points(a: Agent) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    nose_len = AGENT_RADIUS
    edge_len = AGENT_RADIUS

    nose_x = a.x + math.cos(a.angle) * nose_len
    nose_y = a.y + math.sin(a.angle) * nose_len

    left_angle = a.angle + math.pi - math.pi / 4
    right_angle = a.angle + math.pi + math.pi / 4

    back_left = (nose_x + math.cos(left_angle) * edge_len, nose_y + math.sin(left_angle) * edge_len)
    back_right = (nose_x + math.cos(right_angle) * edge_len, nose_y + math.sin(right_angle) * edge_len)

    return (nose_x, nose_y), back_left, back_right


def draw(screen: pygame.Surface, font: pygame.font.Font, sim, gui_driver) -> None:
    screen.fill(UI_BG_COLOR)

    arena_rect = pygame.Rect(0, UI_H, ARENA_W, ARENA_H)
    pygame.draw.rect(screen, BG_COLOR, arena_rect)
    pygame.draw.rect(screen, ARENA_BORDER_COLOR, arena_rect, width=2)

    for obs in sim.world.obstacles:
        pygame.draw.circle(
            screen, OBSTACLE_COLOR, (int(obs.x), int(obs.y + UI_H)), int(obs.r), width=2
        )

    if DEBUG_SHOW:
        for a in sim.agents:
            if not a.alive:
                continue
            cx, cy = int(a.x), int(a.y + UI_H)
            for rel_angle in RAY_ANGLES:
                rx = cx + math.cos(a.angle + rel_angle) * 30 #RAY_MAX_DIST
                ry = cy + math.sin(a.angle + rel_angle) * 30 #RAY_MAX_DIST
                pygame.draw.line(screen, (0, 127, 0), (cx, cy), (rx, ry), width=1)

    for b in sim.bullets:
        pygame.draw.circle(
            screen, BULLET_COLORS[b.team], (int(b.x), int(b.y + UI_H)), BULLET_RADIUS
        )

    for a in sim.agents:
        if not a.alive:
            continue
        cx, cy = int(a.x), int(a.y + UI_H)
        rx = cx + math.cos(a.angle) * AGENT_RADIUS
        ry = cy + math.sin(a.angle) * AGENT_RADIUS
        pygame.draw.line(screen, TEAM_COLORS[a.team], (cx, cy), (rx, ry), width=3)

    blue_alive = sim.team_alive_count(0)
    red_alive = sim.team_alive_count(1)
    hud = (
        f"Gen-{sim.world.generation} "
        f"Frame: {sim.frame}/{FRAMES_PER_GEN} "
        f"Blue: {blue_alive}/{POP_SIZE} "
        f"Red: {red_alive}/{POP_SIZE}"
    )
    text_surf = font.render(hud, True, UI_COLOR)
    screen.blit(text_surf, (10, 10))

    gui_driver.draw(screen, sim.agents, sim.world.generation)

    pygame.display.flip()
