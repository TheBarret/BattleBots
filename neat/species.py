"""Speciation, protects new structure from being outcompeted before it's optimized."""

import random

from genome import Genome, compatibility_distance


class Species:
    def __init__(self, representative: Genome):
        self.representative = representative
        self.members: list[Genome] = [representative]
        self.best_fitness = -float("inf")
        self.generations_since_improvement = 0

    def reset(self) -> None:
        """Called at the start of each generation's speciation pass:
        pick a new representative from last generation's members, then clear
        so this generation's genomes can be reassigned fresh."""
        if self.members:
            self.representative = random.choice(self.members)
        self.members = []

    def add(self, genome: Genome) -> None:
        self.members.append(genome)

    def update_stagnation(self) -> None:
        if not self.members:
            return
        best = max(g.fitness for g in self.members)
        if best > self.best_fitness:
            self.best_fitness = best
            self.generations_since_improvement = 0
        else:
            self.generations_since_improvement += 1

    def adjusted_fitness_sum(self) -> float:
        """Explicit fitness sharing: each member's fitness divided by species
        size, summed. Keeps large species from dominating offspring allocation
        purely by headcount rather than quality."""
        n = len(self.members)
        return sum(g.fitness / n for g in self.members) if n else 0.0


def speciate(genomes: list[Genome], species_list: list[Species], config) -> list[Species]:
    for s in species_list:
        s.reset()

    for g in genomes:
        placed = False
        for s in species_list:
            dist = compatibility_distance(g, s.representative, config.C1_EXCESS, config.C2_DISJOINT, config.C3_WEIGHT)
            if dist < config.COMPAT_THRESHOLD:
                s.add(g)
                placed = True
                break
        if not placed:
            species_list.append(Species(g))

    return [s for s in species_list if s.members]
