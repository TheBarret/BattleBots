# GA Battle Bots Config
import math

# Constants
ARENA_W, ARENA_H    = 750, 750
UI_H                = 40
WINDOW_W, WINDOW_H  = ARENA_W, ARENA_H + UI_H
FPS                 = 60
FRAMES_PER_GEN      = 1100

# Debugger
DEBUG_SHOW          = False

# Checkpoint Settings
CHECKPOINT_BLUE     = "blue.npy"
CHECKPOINT_RED      = "red.npy"
POP_SIZE            = 20
ELITE_COUNT         = 2
TOURNAMENT_SIZE     = 3
TOP_FRACTION        = 0.5
CROSSOVER_GENE_RATE = 0.5

# Calibrated GA Parameters
MUTATION_GENE_RATE  = 0.20
MUTATION_SIGMA      = 0.1

# Audio settings
AUDIO_SFX_ENABLED   = False
AUDIO_SFX_VOLUME    = 0.05
AUDIO_MAX_PLAY      = 512

# Agent Settings
AGENT_RADIUS        = 10
AGENT_SPEED         = 0.85
AGENT_TURN_RATE     = 0.05
AGENT_MAX_HEALTH    = 250.0
AGENT_MAX_COOLDOWN  = 25

AGENT_FIRE_THR      = 0.9
AGENT_BOOST_THR     = 0.1
AGENT_DUAL_USE      = False

# Team Settings
SPAWN_ZONES = [
    (50, 300, 50, 300),
    (ARENA_W - 300, ARENA_W - 50, ARENA_H - 300, ARENA_H - 50),
]

# Booster Config
BOOSTER_MAX_FUEL       = 25.0
BOOSTER_DRAIN_RATE     = 0.4
BOOSTER_RECHARGE_RATE  = 0.1
BOOSTER_SPEED_MULT     = 2.5

# --- Fitness parameters (+) -------------------------------------------
FITNESS_WUR         = 2
FITNESS_DMGD        = 0.5
FITNESS_KILL        = 5.0
FITNESS_FIGHTER     = 0.002
FITNESS_PROX        = 0.003
FITNESS_PROX_MAX    = AGENT_RADIUS + 20

# --- Fitness parameters (-) --------------------------------------------
FITNESS_WALL        = 1.0
FITNESS_SHTF        = 5.5
FITNESS_BOB         = 5.0
FITNESS_TR          = 0.5

# Rotation Penalize Settings
FITNESS_LOW_T       = 0.3
FITNESS_LOW_M       = 0.2

# --- Bullet Settings -----------------------------------------------------
BULLET_SPEED        = 10.0
BULLET_LIFETIME     = 35
BULLET_RADIUS       = 1
BULLET_DAMAGE       = 75.5
BULLET_HIT_RADIUS   = AGENT_RADIUS
BULLET_SPAWN_AT     = AGENT_RADIUS + 2

# Agent Raycast settings
RAY_MAX_DIST = ARENA_W // 3
RAY_ANGLES = [
    -math.pi / 8,
    -math.pi / 16,
     0.0,
     math.pi / 16,
     math.pi / 8,
    -math.pi / 2,
     math.pi / 2,
     math.pi,
]

# Simulator Settings
TEAM_COLORS = [(50, 150, 255), (255, 70, 70)]
BULLET_COLORS = [(150, 195, 255), (255, 150, 150)]
BG_COLOR = (18, 18, 24)
ARENA_BORDER_COLOR = (70, 70, 85)
UI_COLOR = (230, 230, 230)
UI_BG_COLOR = (10, 10, 14)

# Circular Obstacles
OBSTACLE_COUNT = 10
OBSTACLE_MIN_RADIUS = 20
OBSTACLE_MAX_RADIUS = 45
OBSTACLE_COLOR = (90, 90, 105)
OBSTACLE_SPAWN_CLEARANCE = 60
OBSTACLE_MIN_GAP = 20
OBSTACLE_PENALTY_RADIUS = 30.0
OBSTACLE_REGEN_EVERY = 4
OBSTACLE_PLACEMENT_ATTEMPTS = 200

# rev: 0.4
N_IN, N_HID, N_OUT = 36, 38, 4
N_WEIGHTS = N_IN * N_HID + N_HID + N_HID * N_OUT + N_OUT

# rev: 0.5 Map Data (Planned)
#N_IN, N_HID, N_OUT = 44, 46, 4
#N_WEIGHTS = N_IN * N_HID + N_HID + N_HID * N_OUT + N_OUT
