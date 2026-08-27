"""NEAT configuration, isolated testing"""
import math
from dataclasses import dataclass

# Sandbox Settings
FPS = 60
SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 700
COLOR_TEAM_A = (60, 120, 240)    # Blue
COLOR_TEAM_B = (240, 70, 70)     # Red
COLOR_OBSTACLE = (100, 100, 110)
COLOR_BULLET = (255, 220, 0)
COLOR_BG = (25, 25, 30)
# Abilities
MAX_FIRE_COOLDOWN = 15      # Frames (~0.25s)
SHIELD_DURATION = 90        # Frames (~1.5s)
SHIELD_COOLDOWN = 300       # Frames (~5.0s)
BOOST_DURATION = 60         # Frames (~1.0s)
BOOST_COOLDOWN = 240        # Frames (~4.0s)
# Sensor Config
VISION_RADIUS = 300.0
NUM_SECTORS = 5             # Slices across 180-degree front vision arc
FOV_RAD = math.radians(180)


@dataclass
class Config:
    #  Topology
    N_INPUTS: int = 2
    N_OUTPUTS: int = 1
    USE_BIAS: bool = True

    #  Population
    POP_SIZE: int = 150
    SURVIVAL_THRESHOLD: float = 0.2        # fraction of each species allowed to reproduce
    STAGNATION_LIMIT: int = 15             # generations a species can go without improving before culled

    #  Speciation (compatibility distance, per original NEAT paper)
    C1_EXCESS: float = 1.0
    C2_DISJOINT: float = 1.0
    C3_WEIGHT: float = 0.4
    COMPAT_THRESHOLD: float = 3.0

    #  Weight mutation
    WEIGHT_MUTATE_RATE: float = 0.8        # probability a genome's weights get touched at all
    WEIGHT_PERTURB_RATE: float = 0.9       # within that, probability of perturb vs full reset
    WEIGHT_PERTURB_POWER: float = 0.5
    WEIGHT_INIT_SCALE: float = 1.0

    #  Structural mutation
    ADD_CONNECTION_RATE: float = 0.05
    ADD_NODE_RATE: float = 0.03
    DISABLE_INHERITED_RATE: float = 0.75   # if either parent had a gene disabled, chance child inherits disabled

    # Crossover
    CROSSOVER_RATE: float = 0.75           # probability offspring comes from crossover vs mutation-only clone

    # Training / logging (Phase 2)
    MAX_GENERATIONS: int = 300
    EARLY_STOP_FITNESS: float | None = None
    CHECKPOINT_INTERVAL: int = 25

    # Dynamic threshold adjuster
    TARGET_SPECIES = 10

    # Visualization
    #TODO
