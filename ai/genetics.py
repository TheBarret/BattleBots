"""Genetic algorithm operators - selection, crossover, mutation."""

import math
import random
import numpy as np
from ai.network import Network
from config import *


def weight_distance(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b))


def average_diversity(nets: list[Network]) -> float:
    flats = [n.get_flat() for n in nets]
    total, count = 0.0, 0
    for i in range(len(flats)):
        for j in range(i + 1, len(flats)):
            total += weight_distance(flats[i], flats[j])
            count += 1
    return total / count if count else 0.0


def tournament_select(sorted_nets: list[Network]) -> Network:
    pool_size = max(TOURNAMENT_SIZE, math.ceil(len(sorted_nets) * TOP_FRACTION))
    pool = sorted_nets[:pool_size]
    contestants = random.sample(pool, min(TOURNAMENT_SIZE, len(pool)))
    return min(contestants, key=lambda n: pool.index(n))


def crossover(parent_a: Network, parent_b: Network) -> Network:
    a = parent_a.get_flat()
    b = parent_b.get_flat()
    mask = np.random.rand(N_WEIGHTS) < CROSSOVER_GENE_RATE
    child = np.where(mask, b, a)
    return Network(child)


def mutate(net: Network) -> None:
    flat = net.get_flat()
    mask = np.random.rand(N_WEIGHTS) < MUTATION_GENE_RATE
    noise = np.random.randn(N_WEIGHTS) * MUTATION_SIGMA
    flat = flat + mask * noise
    net.set_flat(flat)


def evolve_population(nets: list[Network], fitnesses: list[float]) -> list[Network]:
    order = sorted(range(len(nets)), key=lambda i: fitnesses[i], reverse=True)
    sorted_nets = [nets[i] for i in order]

    next_gen: list[Network] = [n.clone() for n in sorted_nets[:ELITE_COUNT]]

    while len(next_gen) < len(nets):
        parent_a = tournament_select(sorted_nets)
        parent_b = tournament_select(sorted_nets)
        child = crossover(parent_a, parent_b)
        mutate(child)
        next_gen.append(child)

    return next_gen
