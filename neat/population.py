"""Population management and generational evolution."""

import json
from dataclasses import asdict

from innovation import InnovationTracker
from genome import Genome, mutate, crossover
from species import Species, speciate
from config import Config
import random


class Population:
    def __init__(self, config : Config):
        self.config = config
        start_node_id = config.N_INPUTS + config.N_OUTPUTS + (1 if config.USE_BIAS else 0)
        self.tracker = InnovationTracker(start_node_id=start_node_id)

        self.genomes: list[Genome] = [Genome.minimal(config, self.tracker) for _ in range(config.POP_SIZE)]
        self.species_list: list[Species] = []
        self.generation = 0

        self.best_genome: Genome | None = None
        self.best_fitness = -float("inf")
        self.stats = {"avg_fitness": 0.0, "max_fitness": 0.0, "species_count": 0}

        self.history: dict[str, list] = {
            "generation": [],
            "max_fitness": [],
            "avg_fitness": [],
            "min_fitness": [],
            "species_count": [],
            "avg_nodes": [],
            "avg_enabled_connections": [],
            "avg_total_connections": [],
        }

    def evolve(self, fitnesses: list[float]) -> None:
        for g, f in zip(self.genomes, fitnesses):
            g.fitness = f

        gen_best_idx = max(range(len(fitnesses)), key=lambda i: fitnesses[i])
        if fitnesses[gen_best_idx] > self.best_fitness:
            self.best_fitness = fitnesses[gen_best_idx]
            self.best_genome = self.genomes[gen_best_idx].copy()

        self.species_list = speciate(self.genomes, self.species_list, self.config)
        for s in self.species_list:
            s.update_stagnation()

        # cull stagnant species, but never wipe out every species in one pass
        survivors = [s for s in self.species_list if s.generations_since_improvement < self.config.STAGNATION_LIMIT]
        self.species_list = survivors if survivors else self.species_list[:1]

        self.stats = {
            "avg_fitness": sum(fitnesses) / len(fitnesses),
            "max_fitness": max(fitnesses),
            "species_count": len(self.species_list),
        }

        # Dynamic Speciation Threshold (delta-t)
        target_species = self.config.TARGET_SPECIES
        if len(self.species_list) < target_species:
            self.config.COMPAT_THRESHOLD -= 0.1
        elif len(self.species_list) > target_species:
            self.config.COMPAT_THRESHOLD += 0.1
        self.config.COMPAT_THRESHOLD = max(0.3, self.config.COMPAT_THRESHOLD)

        # History recorded here deliberately - AFTER speciate()/culling, not
        # right after fitnesses are assigned. species_count needs the species
        # just computed for *this* generation's genomes, not last generation's
        # leftover self.species_list.
        pop_n = len(self.genomes)
        avg_nodes = sum(len(g.nodes) for g in self.genomes) / pop_n
        avg_enabled = sum(1 for g in self.genomes for c in g.connections.values() if c.enabled) / pop_n
        avg_total_conn = sum(len(g.connections) for g in self.genomes) / pop_n

        self.history["generation"].append(self.generation)
        self.history["max_fitness"].append(self.stats["max_fitness"])
        self.history["avg_fitness"].append(self.stats["avg_fitness"])
        self.history["min_fitness"].append(min(fitnesses))
        self.history["species_count"].append(self.stats["species_count"])
        self.history["avg_nodes"].append(avg_nodes)
        self.history["avg_enabled_connections"].append(avg_enabled)
        self.history["avg_total_connections"].append(avg_total_conn)

        total_adjusted = sum(s.adjusted_fitness_sum() for s in self.species_list)
        next_genomes: list[Genome] = []
        for s in self.species_list:
            share = s.adjusted_fitness_sum() / total_adjusted if total_adjusted > 0 else 1 / len(self.species_list)
            n_offspring = max(1, round(share * self.config.POP_SIZE))
            next_genomes.extend(self._reproduce_species(s, n_offspring))

        next_genomes = next_genomes[: self.config.POP_SIZE]
        while len(next_genomes) < self.config.POP_SIZE:
            filler = random.choice(self.genomes).copy()
            mutate(filler, self.tracker, self.config)
            next_genomes.append(filler)

        self.genomes = next_genomes
        self.tracker.reset_generation_cache()
        self.generation += 1

    def _reproduce_species(self, species: Species, n_offspring: int) -> list[Genome]:
        members = sorted(species.members, key=lambda g: g.fitness, reverse=True)
        n_survivors = max(1, int(len(members) * self.config.SURVIVAL_THRESHOLD))
        survivors = members[:n_survivors]

        offspring: list[Genome] = [members[0].copy()]  # elitism: species champion survives unmutated

        while len(offspring) < n_offspring:
            if len(survivors) > 1 and random.random() < self.config.CROSSOVER_RATE:
                a, b = random.sample(survivors, 2)
                child = crossover(a, b, self.tracker, self.config)
            else:
                child = random.choice(survivors).copy()
            mutate(child, self.tracker, self.config)
            offspring.append(child)

        return offspring[:n_offspring]

    # ---- checkpointing --------------------------------------------------

    def save_checkpoint(self, path: str) -> None:
        data = {
            "generation": self.generation,
            "best_fitness": self.best_fitness,
            "best_genome": self.best_genome.to_dict() if self.best_genome else None,
            "genomes": [g.to_dict() for g in self.genomes],
            "tracker": {
                "node_counter": self.tracker._node_counter,
                "innovation_counter": self.tracker._innovation_counter,
            },
            "config": asdict(self.config),
            "history": self.history,
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_checkpoint(cls, path: str, config) -> "Population":
        """Restores genomes, tracker, and history. Species list is NOT
        restored (deliberate - see design discussion); speciation rebuilds
        fresh on the next evolve() call.

        config's topology fields (N_INPUTS/N_OUTPUTS/USE_BIAS) must match
        what the checkpoint was saved with - other hyperparameters (mutation
        rates, etc.) are free to differ on resume.
        """
        with open(path) as f:
            data = json.load(f)

        saved_topology = data["config"]
        for key in ("N_INPUTS", "N_OUTPUTS", "USE_BIAS"):
            if saved_topology.get(key) != getattr(config, key):
                raise ValueError(
                    f"Checkpoint topology mismatch on {key}: "
                    f"checkpoint has {saved_topology.get(key)!r}, config has {getattr(config, key)!r}. "
                    "Genomes reference fixed input/output node ids tied to this topology."
                )

        start_node_id = config.N_INPUTS + config.N_OUTPUTS + (1 if config.USE_BIAS else 0)
        tracker = InnovationTracker(start_node_id=start_node_id)

        # Defensive floor on BOTH counters against what's actually present in
        # the loaded genomes, not just the saved counter values - guards
        # against a hand-edited or merged checkpoint causing an id collision.
        max_node = start_node_id - 1
        max_innovation = -1
        for g_data in data["genomes"]:
            for n in g_data["nodes"]:
                max_node = max(max_node, n["id"])
            for c in g_data["connections"]:
                max_innovation = max(max_innovation, c["innovation"])

        tracker._node_counter = max(data["tracker"]["node_counter"], max_node + 1)
        tracker._innovation_counter = max(data["tracker"]["innovation_counter"], max_innovation + 1)

        # Bypass __init__'s random-population construction (POP_SIZE calls to
        # Genome.minimal that would just be thrown away) - build the shell
        # directly and populate it from the checkpoint instead.
        pop = cls.__new__(cls)
        pop.config = config
        pop.tracker = tracker
        pop.species_list = []
        pop.generation = data["generation"]
        pop.best_fitness = data["best_fitness"]
        pop.best_genome = Genome.from_dict(data["best_genome"], config, tracker) if data["best_genome"] else None
        pop.genomes = [Genome.from_dict(g, config, tracker) for g in data["genomes"]]
        pop.stats = {"avg_fitness": 0.0, "max_fitness": 0.0, "species_count": 0}
        pop.history = data.get("history", {k: [] for k in [
            "generation", "max_fitness", "avg_fitness", "min_fitness",
            "species_count", "avg_nodes", "avg_enabled_connections", "avg_total_connections",
        ]})

        return pop
