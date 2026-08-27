"""NEAT genome: graph-based, variable topology, feedforward-only (v1)."""

import math
import random
from collections import deque

from genes import NodeGene, ConnectionGene, NodeType
from innovation import InnovationTracker


class Genome:
    def __init__(self, config, tracker: InnovationTracker):
        self.config = config
        self.tracker = tracker
        self.nodes: dict[int, NodeGene] = {}
        self.connections: dict[int, ConnectionGene] = {}
        self.fitness = 0.0

    def to_dict(self) -> dict:
        return {
            "nodes": [{"id": n.id, "type": n.type.name} for n in self.nodes.values()],
            "connections": [
                {
                    "in_node": c.in_node,
                    "out_node": c.out_node,
                    "weight": c.weight,
                    "enabled": c.enabled,
                    "innovation": c.innovation,
                }
                for c in self.connections.values()
            ],
            "fitness": self.fitness,
        }

    @classmethod
    def from_dict(cls, data: dict, config, tracker: InnovationTracker) -> "Genome":
        g = cls(config, tracker)
        g.fitness = data.get("fitness", 0.0)
        for n in data["nodes"]:
            g.nodes[n["id"]] = NodeGene(n["id"], NodeType[n["type"]])
        for c in data["connections"]:
            g.connections[c["innovation"]] = ConnectionGene(
                c["in_node"], c["out_node"], c["weight"], c["enabled"], c["innovation"]
            )
        return g

    # ---- construction ----------------------------------------------------

    @classmethod
    def minimal(cls, config, tracker: InnovationTracker) -> "Genome":
        """Minimal starting topology: inputs (+bias) fully connected to outputs, no hidden nodes.

        Input/output/bias node ids are fixed and reserved (0..n_inputs-1 for
        inputs, then bias, then outputs) rather than drawn from the tracker,
        so every genome in the initial population - and the tracker's hidden
        node ids later - refer to the same sensor/output slots consistently.
        """
        g = cls(config, tracker)

        input_ids = list(range(config.N_INPUTS))
        for nid in input_ids:
            g.nodes[nid] = NodeGene(nid, NodeType.INPUT)

        bias_ids = []
        if config.USE_BIAS:
            bias_id = config.N_INPUTS
            bias_ids = [bias_id]
            g.nodes[bias_id] = NodeGene(bias_id, NodeType.BIAS)

        out_start = config.N_INPUTS + (1 if config.USE_BIAS else 0)
        output_ids = list(range(out_start, out_start + config.N_OUTPUTS))
        for nid in output_ids:
            g.nodes[nid] = NodeGene(nid, NodeType.OUTPUT)

        for i in input_ids + bias_ids:
            for o in output_ids:
                innov = tracker.get_connection_innovation(i, o)
                weight = random.uniform(-1, 1) * config.WEIGHT_INIT_SCALE
                g.connections[innov] = ConnectionGene(i, o, weight, True, innov)

        return g

    def copy(self) -> "Genome":
        g = Genome(self.config, self.tracker)
        g.nodes = {nid: NodeGene(n.id, n.type) for nid, n in self.nodes.items()}
        g.connections = {innov: c.copy() for innov, c in self.connections.items()}
        return g

    # ---- node id helpers ----------------------------------------------------

    @property
    def input_ids(self) -> list[int]:
        return [n.id for n in self.nodes.values() if n.type == NodeType.INPUT]

    @property
    def bias_ids(self) -> list[int]:
        return [n.id for n in self.nodes.values() if n.type == NodeType.BIAS]

    @property
    def output_ids(self) -> list[int]:
        return [n.id for n in self.nodes.values() if n.type == NodeType.OUTPUT]

    # ---- phenotype evaluation ----------------------------------------------

    def activate(self, inputs: list[float]) -> list[float]:
        in_ids = self.input_ids
        assert len(inputs) == len(in_ids), f"expected {len(in_ids)} inputs, got {len(inputs)}"

        values: dict[int, float] = {}
        for nid, x in zip(sorted(in_ids), inputs):
            values[nid] = x
        for nid in self.bias_ids:
            values[nid] = 1.0

        for nid in self._topological_order():
            if nid in values:
                continue
            incoming = [c for c in self.connections.values() if c.enabled and c.out_node == nid]
            total = sum(values.get(c.in_node, 0.0) * c.weight for c in incoming)
            values[nid] = math.tanh(total)

        return [values.get(nid, 0.0) for nid in sorted(self.output_ids)]

    def _topological_order(self) -> list[int]:
        """Kahn's algorithm. Valid as long as mutate_add_connection's cycle
        check has held - this genome is a DAG by construction."""
        in_degree = {nid: 0 for nid in self.nodes}
        adj: dict[int, list[int]] = {nid: [] for nid in self.nodes}
        for c in self.connections.values():
            if not c.enabled:
                continue
            adj[c.in_node].append(c.out_node)
            in_degree[c.out_node] += 1

        queue = deque(nid for nid, d in in_degree.items() if d == 0)
        order = []
        while queue:
            n = queue.popleft()
            order.append(n)
            for m in adj[n]:
                in_degree[m] -= 1
                if in_degree[m] == 0:
                    queue.append(m)
        return order

    def _creates_cycle(self, in_node: int, out_node: int) -> bool:
        """Would adding edge in_node -> out_node create a cycle?
        Equivalent to: can out_node already reach in_node?"""
        if in_node == out_node:
            return True
        visited = set()
        stack = [out_node]
        while stack:
            n = stack.pop()
            if n == in_node:
                return True
            if n in visited:
                continue
            visited.add(n)
            for c in self.connections.values():
                if c.enabled and c.in_node == n:
                    stack.append(c.out_node)
        return False

    # ---- mutation -----------------------------------------------------------

    def mutate_weights(self, config) -> None:
        for conn in self.connections.values():
            if random.random() < config.WEIGHT_PERTURB_RATE:
                conn.weight += random.gauss(0, 1) * config.WEIGHT_PERTURB_POWER
            else:
                conn.weight = random.uniform(-1, 1) * config.WEIGHT_INIT_SCALE

    def mutate_add_connection(self, tracker: InnovationTracker, config, max_attempts: int = 20) -> None:
        node_ids = list(self.nodes.keys())
        for _ in range(max_attempts):
            a = random.choice(node_ids)
            b = random.choice(node_ids)
            if self.nodes[a].type == NodeType.OUTPUT:
                continue
            if self.nodes[b].type in (NodeType.INPUT, NodeType.BIAS):
                continue
            if a == b:
                continue

            existing = next(
                (c for c in self.connections.values() if c.in_node == a and c.out_node == b), None
            )
            if existing is not None:
                if not existing.enabled:
                    existing.enabled = True
                    return
                continue

            if self._creates_cycle(a, b):
                continue

            innov = tracker.get_connection_innovation(a, b)
            weight = random.uniform(-1, 1) * config.WEIGHT_INIT_SCALE
            self.connections[innov] = ConnectionGene(a, b, weight, True, innov)
            return
        # exhausted attempts (genome likely near-fully-connected for its size) - no-op

    def mutate_add_node(self, tracker: InnovationTracker, config) -> None:
        enabled = [c for c in self.connections.values() if c.enabled]
        if not enabled:
            return
        conn = random.choice(enabled)
        conn.enabled = False

        new_id = tracker.get_node_id_for_split(conn.innovation)
        self.nodes[new_id] = NodeGene(new_id, NodeType.HIDDEN)

        innov_in = tracker.get_connection_innovation(conn.in_node, new_id)
        innov_out = tracker.get_connection_innovation(new_id, conn.out_node)
        # in->new gets weight 1.0, new->out inherits the old weight - the classic
        # NEAT split, which makes the mutation near-fitness-neutral at first
        self.connections[innov_in] = ConnectionGene(conn.in_node, new_id, 1.0, True, innov_in)
        self.connections[innov_out] = ConnectionGene(new_id, conn.out_node, conn.weight, True, innov_out)

def mutate(genome: Genome, tracker: InnovationTracker, config) -> None:
    if random.random() < config.WEIGHT_MUTATE_RATE:
        genome.mutate_weights(config)
    if random.random() < config.ADD_CONNECTION_RATE:
        genome.mutate_add_connection(tracker, config)
    if random.random() < config.ADD_NODE_RATE:
        genome.mutate_add_node(tracker, config)


# ---- crossover and compatibility (operate on pairs of genomes) --------------


def crossover(parent_a: Genome, parent_b: Genome, tracker: InnovationTracker, config) -> Genome:
    """Align genes by innovation number. Matching genes: random parent.
    Disjoint/excess: always from the fitter parent (equal fitness -> parent_a)."""
    if parent_b.fitness > parent_a.fitness:
        parent_a, parent_b = parent_b, parent_a

    child = Genome(config, tracker)
    for innov, conn_a in parent_a.connections.items():
        conn_b = parent_b.connections.get(innov)
        if conn_b is not None:
            chosen = random.choice([conn_a, conn_b])
            new_conn = chosen.copy()
            if (not conn_a.enabled or not conn_b.enabled) and random.random() < config.DISABLE_INHERITED_RATE:
                new_conn.enabled = False
            else:
                new_conn.enabled = True
        else:
            new_conn = conn_a.copy()  # disjoint/excess from fitter parent
        child.connections[innov] = new_conn

    referenced = set()
    for c in child.connections.values():
        referenced.add(c.in_node)
        referenced.add(c.out_node)
    for nid in referenced:
        source = parent_a.nodes.get(nid) or parent_b.nodes.get(nid)
        child.nodes[nid] = NodeGene(nid, source.type)

    # safety net: always carry forward every fixed input/output/bias node,
    # even if (unusually) no inherited connection references it
    for nid, node in parent_a.nodes.items():
        if node.type in (NodeType.INPUT, NodeType.OUTPUT, NodeType.BIAS):
            child.nodes.setdefault(nid, NodeGene(nid, node.type))

    return child


def compatibility_distance(a: Genome, b: Genome, c1: float, c2: float, c3: float) -> float:
    innov_a = set(a.connections.keys())
    innov_b = set(b.connections.keys())
    matching = innov_a & innov_b

    max_a = max(innov_a) if innov_a else 0
    max_b = max(innov_b) if innov_b else 0
    low_max = min(max_a, max_b)

    disjoint = 0
    excess = 0
    for i in innov_a ^ innov_b:
        if i > low_max:
            excess += 1
        else:
            disjoint += 1

    if matching:
        weight_diff = sum(abs(a.connections[i].weight - b.connections[i].weight) for i in matching) / len(matching)
    else:
        weight_diff = 0.0

    n = max(len(innov_a), len(innov_b))
    n = 1 if n < 20 else n  # per original paper: skip normalization for small genomes

    return (c1 * excess / n) + (c2 * disjoint / n) + (c3 * weight_diff)
