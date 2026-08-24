"""Population management, evolution, and checkpointing."""

import os
import numpy as np
from ai.network import Network
from ai.genetics import evolve_population, average_diversity, mutate
from config import *


class Population:
    """Manages a population of neural networks for one team."""

    def __init__(self, team: int, checkpoint_path: str):
        self.team = team
        self.checkpoint_path = checkpoint_path
        self.nets: list[Network] = []
        self.best_fitness = -1.0
        self.stats = {"avg_fitness": 0.0, "max_fitness": 0.0, "diversity": 0.0, "alive": POP_SIZE}
        self._initialize(checkpoint_path)

    def _initialize(self, path: str) -> None:
        """Load checkpoint or create random population."""
        if os.path.exists(path):
            try:
                best_weights = np.load(path)
                self.nets = [Network(best_weights.copy())]
                for _ in range(POP_SIZE - 1):
                    variant = Network(best_weights.copy())
                    mutate(variant)
                    self.nets.append(variant)
                print(f"[snapshot] Team {self.team} initialized from {path}")
                return
            except Exception as e:
                print(f"[error] Failed to load {path}: {e}")

        self.nets = [Network() for _ in range(POP_SIZE)]

    def evolve(self, fitnesses: list[float], generation: int, warmup: int) -> None:
        """Evolve population using fitness scores."""
        max_fit = float(np.max(fitnesses))

        if max_fit > self.best_fitness and generation > warmup:
            self.best_fitness = max_fit
            best_idx = int(np.argmax(fitnesses))
            best_weights = self.nets[best_idx].get_flat()
            np.save(self.checkpoint_path, best_weights)
            print(f"[snapshot] Team {self.team} reached fitness {max_fit:.1f} ({self.checkpoint_path})")

        self.stats = {
            "avg_fitness": float(np.mean(fitnesses)),
            "max_fitness": max_fit,
            "diversity": average_diversity(self.nets),
            "alive": self.stats["alive"],
        }

        self.nets = evolve_population(self.nets, fitnesses)
