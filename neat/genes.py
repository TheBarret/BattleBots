"""Gene definitions for NEAT genomes."""

from dataclasses import dataclass
from enum import Enum, auto


class NodeType(Enum):
    INPUT = auto()
    BIAS = auto()
    HIDDEN = auto()
    OUTPUT = auto()


@dataclass
class NodeGene:
    id: int
    type: NodeType


@dataclass
class ConnectionGene:
    in_node: int
    out_node: int
    weight: float
    enabled: bool
    innovation: int

    def copy(self) -> "ConnectionGene":
        return ConnectionGene(self.in_node, self.out_node, self.weight, self.enabled, self.innovation)
