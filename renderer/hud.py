import pygame
from config import *
from models import Agent


class GUI:
    def __init__(self, x=530, y=10, width=210, height=200):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = pygame.font.SysFont("Consolas", 12)
        self.title_font = pygame.font.SysFont("Consolas", 14, bold=True)

    def draw(self, screen, agents, gen_number):
        active_agents = [a for a in agents if a.alive]
        if not active_agents:
            active_agents = agents

        best_bot = max(active_agents, key=lambda a: a.fitness())

        panel = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        panel.fill((10, 12, 18, 210))
        screen.blit(panel, (self.rect.x, self.rect.y))
        pygame.draw.rect(screen, (70, 130, 240), self.rect, width=1, border_radius=4)

        if best_bot.alive:
            pygame.draw.line(screen, (255, 225, 0), (self.rect.x, self.rect.height), (best_bot.x, best_bot.y))

        team_str = "BLUE" if best_bot.team == 0 else "RED"
        team_color = (100, 180, 255) if best_bot.team == 0 else (255, 100, 100)

        lines = [
            ("LEADER TELEMETRY", (230, 230, 230), True),
            (f"Gen: {gen_number} | Team: {team_str}", team_color, False),
            (f"Fitness:   {best_bot.fitness():.1f}", (255, 215, 0), False),
            (f"Damage:    {best_bot.damage_dealt:.0f}", (220, 220, 220), False),
            (f"Kills:     {best_bot.kills}", (220, 220, 220), False),
            (f"Shots:     {best_bot.shots_fired}", (220, 220, 220), False),
            (f"Accuracy:  {self._get_accuracy(best_bot):.1f}%", (220, 220, 220), False),
        ]

        curr_y = self.rect.y + 8
        for text, color, is_header in lines:
            f = self.title_font if is_header else self.font
            lbl = f.render(text, True, color)
            screen.blit(lbl, (self.rect.x + 10, curr_y))
            curr_y += 18 if not is_header else 22

        curr_y += 4
        self._draw_bar(screen, "HP", self.rect.x + 10, curr_y, 190, 8,
                       best_bot.health / 100.0, (50, 205, 50))
        curr_y += 16

        boost_ratio = getattr(best_bot, 'boost_fuel', 30.0) / 30.0
        self._draw_bar(screen, "BOOST", self.rect.x + 10, curr_y, 190, 8,
                       boost_ratio, (27, 91, 127))

    def _get_accuracy(self, agent):
        if agent.shots_fired == 0:
            return 0.0
        return (agent.hits_landed / agent.shots_fired) * 100.0

    def _draw_bar(self, screen, label, x, y, width, height, ratio, color):
        lbl = self.font.render(label, True, (160, 160, 160))
        screen.blit(lbl, (x, y - 2))

        bar_x = x + 42
        bar_w = width - 42
        ratio = max(0.0, min(1.0, ratio))

        pygame.draw.rect(screen, (40, 40, 50), (bar_x, y, bar_w, height), border_radius=2)
        if ratio > 0:
            pygame.draw.rect(screen, color, (bar_x, y, int(bar_w * ratio), height), border_radius=2)
