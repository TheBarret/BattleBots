import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame
from config import *
from audio import SoundBits
from core.world import World
from core.simulation import Simulation
from ai.population import Population
from renderer.renderer import draw
from renderer.hud import GUI


class GABattleBots:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("GA Battle Bots")
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 18)
        if self.font is None:
            self.font = pygame.font.Font(None, 20)

        self.audio = SoundBits()
        self.world = World()
        self.sim = Simulation(self.world, self.audio)

        self.populations = [
            Population(0, CHECKPOINT_BLUE),
            Population(1, CHECKPOINT_RED)
        ]

        self.hud = GUI(x=ARENA_W - 220, y=10, width=210, height=185)

        self._reset_generation()
        self.running = True

    def _reset_generation(self) -> None:
        team_nets = [pop.nets for pop in self.populations]
        self.sim.reset(team_nets)

    def run(self) -> None:
        while self.running:
            skip = self._handle_events()

            if not self.running:
                break

            self.sim.step()
            draw(self.screen, self.font, self.sim, self.hud)
            self.clock.tick(FPS)

            if skip or self.sim.generation_over():
                self._evolve()

    def _handle_events(self) -> bool:
        skip = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    skip = True
        return skip

    def _evolve(self) -> None:
        for team in range(2):
            team_agents = [a for a in self.sim.agents if a.team == team]
            fitnesses = [a.fitness() for a in team_agents]
            self.populations[team].evolve(
                fitnesses,
                self.world.generation,
                FITNESS_WUR
            )
            self.populations[team].stats["alive"] = self.sim.team_alive_count(team)

        self._print_stats()

        self.world.generation += 1

        if self._should_regenerate_obstacles():
            self.world.regenerate_obstacles()

        self._reset_generation()

    def _should_regenerate_obstacles(self) -> bool:
        if OBSTACLE_REGEN_EVERY == 0:
            return True
        if OBSTACLE_REGEN_EVERY > 0 and self.world.generation % OBSTACLE_REGEN_EVERY == 0:
            return True
        return False

    def _print_stats(self) -> None:
        print(f"[Gen {self.world.generation - 1:>4}]:")
        for team, pop in enumerate(self.populations):
            name = "Blue" if team == 0 else "Red"
            s = pop.stats
            print(f"- {name}: alive={s['alive']:>2}/{POP_SIZE} "
                  f"avgFit={s['avg_fitness']:.1f} "
                  f"maxFit={s['max_fitness']:.1f} "
                  f"div={s['diversity']:.2f}")


def main():
    game = GABattleBots()
    game.run()
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
