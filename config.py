# GA Battle Bots Config
import math

# Constants
ARENA_W, ARENA_H    = 750, 750
UI_H                = 40
WINDOW_W, WINDOW_H  = ARENA_W, ARENA_H + UI_H
FPS                 = 60
FRAMES_PER_GEN      = 800

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
MUTATION_GENE_RATE  = 0.25
MUTATION_SIGMA      = 0.1

# Audio settings
AUDIO_SFX_ENABLED   = False   # Audio switch
AUDIO_SFX_VOLUME    = 0.05   # offset volume for sfx channels
AUDIO_MAX_PLAY      = 128   # play max of AUDIO_MAX_PLAY samples per frame


# Agent Settings
AGENT_RADIUS        = 10
AGENT_SPEED         = 0.85
AGENT_TURN_RATE     = 0.15
AGENT_MAX_HEALTH    = 250.0
AGENT_MAX_COOLDOWN  = 15
AGENT_FIRE_THR      = 0.75 # fire weight threshold
AGENT_BOOST_THR     = 0.25 # booster weight threshold
AGENT_DUAL_USE      = False # shoot & boost at the same time

# Team Settings
#SPAWN_ZONES = [ # SPAWN_ZONES format: (x_min, x_max, y_min, y_max)
#    (50, 300, 50, 300),
#    (ARENA_W - 300, ARENA_W - 50, 300, ARENA_H - 50),
#]
SPAWN_ZONES = [
    (50, 300, 50, 300),
    (ARENA_W - 300, ARENA_W - 50, ARENA_H - 300, ARENA_H - 50),
]

# Booster Config
BOOSTER_MAX_FUEL    = 25.0              # Total fuel capacity (frames of continuous boost)
BOOSTER_DRAIN_RATE  = 0.4               # Fuel consumed per boosted frame
BOOSTER_RECHARGE_RATE = 0.1             # Recharge rate per frame when not boosting
BOOSTER_SPEED_MULT  = 3.0           # Speed base multiplier when boosting (base + neuron_output)

# Fitness parameters (+)
FITNESS_WUR         = 2            # Warm-up round (Snapshot when iterations > FITNESS_WUR) (!)
FITNESS_DMGD        = 1.5         # Reward for hitting enemies (+)
FITNESS_KILL        = 2.0         # Flat bonus for eliminating an enemy (+)
FITNESS_FIGHTER     = 0.03         # Flat small bonus for active engagment (+)
FITNESS_PROX        = 0.03         # Reward closing distance to enemies (+)
FITNESS_PROX_MAX    = 45        # stop rewarding when distance is less then radius (switch)

# Fitness parameters (-)
FITNESS_WALL        = 2.0         # Penalty for hugging walls (-)
FITNESS_SHTF        = 3.0         # Cost per shot-and-missed spendure penalty (-)
FITNESS_BOB         = 2.0         # Penalty blue on blue hits (-)
FITNESS_TR          = 1.0         # Forever Rotation penalty (LOW_T/LOW_M) (-)

# Rotation Penalize Settings
FITNESS_LOW_T       = 0.3   # lowest turn
FITNESS_LOW_M       = 0.2   # lowest movement

# Bullet Settings
BULLET_SPEED        = 10.0
BULLET_LIFETIME     = 35
BULLET_RADIUS       = 1
BULLET_DAMAGE       = 25
BULLET_HIT_RADIUS   = AGENT_RADIUS
BULLET_SPAWN_AT     = AGENT_RADIUS + 10

# Agent Raycast settings
# rev 0.2: Layered (5) Primary (Forward Arc) + 3 Secondary (Sides & Rear)
RAY_MAX_DIST = ARENA_W // 2
RAY_ANGLES = [
    # Primary Arc (Targeting & Ahead Detection)
    -math.pi / 8,     # Forward-Left Outer
    -math.pi / 16,    # Forward-Left Inner
     0.0,             # Center
     math.pi / 16,    # Forward-Right Inner
     math.pi / 8,     # Forward-Right Outer
    # Secondary Arc (Core Spatial & Flank Awareness)
    -math.pi / 2,     # Left Flank (-90°)
     math.pi / 2,     # Right Flank (+90°)
     math.pi,         # Rear (180°)
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
OBSTACLE_SPAWN_CLEARANCE = 60   # keep obstacles clear of spawn zone rectangles
OBSTACLE_MIN_GAP = 20           # min gap between obstacle edges when placing
OBSTACLE_PENALTY_RADIUS = 30.0  # same "hugging" penalty zone width as walls
OBSTACLE_REGEN_EVERY = 4        # regenerate layout every N generations (0 = every gen, -1 = never after first)
OBSTACLE_PLACEMENT_ATTEMPTS = 200

# rev: 0.4
# 8 Rays * 4 Channels (32) + Health + Cooldown + Boost Charge + Bias = 36 Inputs (booster added)
# Outputs: Move, Turn, Shoot, Boost = 4 Outputs
N_IN, N_HID, N_OUT = 36, 38, 4  #38-38-4 default
N_WEIGHTS = N_IN * N_HID + N_HID + N_HID * N_OUT + N_OUT

# rev: 0.5 Map Data
# 8 Rays * 5 Channels (Wall, Enemy, Teammate, Bullet, Death) = 40
# + Health + Cooldown + Boost Charge + Bias = 44 Inputs
# Outputs: Move, Turn, Shoot, Boost = 4 Outputs
#N_IN, N_HID, N_OUT = 44, 46, 4
#N_WEIGHTS = N_IN * N_HID + N_HID + N_HID * N_OUT + N_OUT
