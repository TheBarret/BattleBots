"""Training orchestration.
Deliberately minimal:
- Population is the state machine
- Trainer just drives the generation loop, evaluation, and early stopping.

Trainer does not know about the visualizer, if a callback is supplied,
it's called with (population, generation) and can do whatever it wants
(render, log, save extra checkpoints) without Trainer needing to know what that is.
"""

from typing import Callable, Optional

from config import Config
from genome import Genome
from population import Population


class Trainer:
    def __init__(self, config: Config, evaluate_fn: Callable[[Genome], float], population: Optional[Population] = None):
        self.config = config
        self.evaluate_fn = evaluate_fn
        # Accept a pre-built Population (e.g. from Population.load_checkpoint)
        # so a resumed run doesn't have to throw away restored state.
        self.population = population if population is not None else Population(config)

    @property
    def generation(self) -> int:
        # Population already owns this counter, Trainer reads it rather
        # than keeping a second copy that could drift out of sync,
        # particularly across a checkpoint resume.
        return self.population.generation

    def train(self, generations: Optional[int] = None, callback: Optional[Callable[[Population, int], None]] = None) -> Genome:
        max_gen = self.generation + (generations if generations is not None else self.config.MAX_GENERATIONS)

        while self.generation < max_gen:
            fitnesses = [self.evaluate_fn(g) for g in self.population.genomes]
            self.population.evolve(fitnesses)

            if callback is not None:
                callback(self.population, self.generation)

            if self._should_stop():
                break

        return self.population.best_genome

    def _should_stop(self) -> bool:
        if self.config.EARLY_STOP_FITNESS is not None:
            return self.population.best_fitness >= self.config.EARLY_STOP_FITNESS
        return False
