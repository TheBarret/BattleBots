import math
import random
import sys
import pygame

# Import your existing NEAT modules
from config import *
from population import Population

#  Geometry & Perception Helpers

def line_intersects_circle(p1: tuple[float, float], p2: tuple[float, float],
                           center: tuple[float, float], radius: float) -> bool:
    """Fast ray-circle line segment intersection test for obstacle occlusion."""
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    fx, fy = p1[0] - center[0], p1[1] - center[1]
    a = dx * dx + dy * dy
    if a == 0:
        return False
    b = 2 * (fx * dx + fy * dy)
    c = (fx * fx + fy * fy) - radius * radius
    discriminant = b * b - 4 * a * c
    if discriminant < 0:
        return False
    discriminant = math.sqrt(discriminant)
    t1 = (-b - discriminant) / (2 * a)
    t2 = (-b + discriminant) / (2 * a)
    return (0 <= t1 <= 1) or (0 <= t2 <= 1)


#  Simulation Entities

class Obstacle:
    def __init__(self, x: float, y: float, radius: float):
        self.x = x
        self.y = y
        self.radius = radius

    def draw(self, surface):
        pygame.draw.circle(surface, COLOR_OBSTACLE, (int(self.x), int(self.y)), int(self.radius))


class Bullet:
    def __init__(self, x: float, y: float, angle: float, owner_team: int):
        self.x = x
        self.y = y
        self.speed = 9.0
        self.vx = math.cos(angle) * self.speed
        self.vy = math.sin(angle) * self.speed
        self.owner_team = owner_team
        self.radius = 3.0
        self.alive = True

    def update(self, obstacles):
        self.x += self.vx
        self.y += self.vy

        # Screen boundary check
        if not (0 <= self.x <= SCREEN_WIDTH and 0 <= self.y <= SCREEN_HEIGHT):
            self.alive = False
            return

        # Obstacle collision
        for obs in obstacles:
            if math.hypot(self.x - obs.x, self.y - obs.y) <= obs.radius + self.radius:
                self.alive = False
                return

    def draw(self, surface):
        pygame.draw.circle(surface, COLOR_BULLET, (int(self.x), int(self.y)), int(self.radius))


class Bot:
    def __init__(self, x: float, y: float, angle: float, team: int, brain):
        self.x = x
        self.y = y
        self.angle = angle
        self.team = team
        self.brain = brain
        self.radius = 12.0
        self.hp = 100.0
        self.alive = True

        # Cooldowns & Active States
        self.fire_cd = 0
        self.shield_cd = 0
        self.shield_active = 0
        self.boost_cd = 0
        self.boost_active = 0

        # Performance Tracking for NEAT Fitness
        self.damage_dealt = 0.0
        self.survival_time = 0

    def get_sensors(self, all_bots: list["Bot"], obstacles: list[Obstacle], bullets: list[Bullet]) -> list[float]:
        """Hybrid Multi-Sector Perception System."""
        # 1. State normalization
        inputs = [
            self.hp / 100.0,
            self.shield_cd / SHIELD_COOLDOWN,
            self.boost_cd / BOOST_COOLDOWN,
            self.fire_cd / MAX_FIRE_COOLDOWN,
        ]

        # 2. Initialize Radar Arrays for 5 Slices
        enemy_sectors = [0.0] * NUM_SECTORS
        obstacle_sectors = [0.0] * NUM_SECTORS

        # Process nearby bots (Enemies)
        for other in all_bots:
            if not other.alive or other.team == self.team or other is self:
                continue
            dx, dy = other.x - self.x, other.y - self.y
            dist = math.hypot(dx, dy)
            if dist > VISION_RADIUS:
                continue

            # Check if line of sight is blocked by an obstacle
            blocked = any(
                line_intersects_circle((self.x, self.y), (other.x, other.y), (obs.x, obs.y), obs.radius)
                for obs in obstacles
            )
            if blocked:
                continue

            # Calculate relative angle
            rel_angle = math.atan2(dy, dx) - self.angle
            rel_angle = (rel_angle + math.pi) % (2 * math.pi) - math.pi  # Wrap to [-pi, pi]

            if -FOV_RAD / 2 <= rel_angle <= FOV_RAD / 2:
                # Map to sector index [0 .. NUM_SECTORS - 1]
                norm_angle = (rel_angle + FOV_RAD / 2) / FOV_RAD
                sector_idx = min(int(norm_angle * NUM_SECTORS), NUM_SECTORS - 1)
                proximity = 1.0 - (dist / VISION_RADIUS)
                enemy_sectors[sector_idx] = max(enemy_sectors[sector_idx], proximity)

        # Process Obstacles
        for obs in obstacles:
            dx, dy = obs.x - self.x, obs.y - self.y
            dist = max(0.1, math.hypot(dx, dy) - obs.radius)
            if dist > VISION_RADIUS:
                continue

            rel_angle = math.atan2(dy, dx) - self.angle
            rel_angle = (rel_angle + math.pi) % (2 * math.pi) - math.pi

            if -FOV_RAD / 2 <= rel_angle <= FOV_RAD / 2:
                norm_angle = (rel_angle + FOV_RAD / 2) / FOV_RAD
                sector_idx = min(int(norm_angle * NUM_SECTORS), NUM_SECTORS - 1)
                proximity = 1.0 - (dist / VISION_RADIUS)
                obstacle_sectors[sector_idx] = max(obstacle_sectors[sector_idx], proximity)

        inputs.extend(enemy_sectors)
        inputs.extend(obstacle_sectors)
        return inputs  # Total: 4 state + 5 enemy + 5 obstacle = 14 Inputs

    def update(self, outputs: list[float], new_bullets: list[Bullet], obstacles: list[Obstacle]):
        if not self.alive:
            return

        self.survival_time += 1

        # Decrement cooldowns
        self.fire_cd = max(0, self.fire_cd - 1)
        self.shield_cd = max(0, self.shield_cd - 1)
        self.boost_cd = max(0, self.boost_cd - 1)
        self.shield_active = max(0, self.shield_active - 1)
        self.boost_active = max(0, self.boost_active - 1)

        # Parse Neural Outputs
        drive = outputs[0]               # [-1, 1]
        steer = outputs[1]               # [-1, 1]
        want_fire = outputs[2] > 0.3
        want_shield = outputs[3] > 0.5
        want_boost = outputs[4] > 0.5

        # Steering & Rotation
        self.angle += steer * 0.08
        self.angle %= (2 * math.pi)

        # Speed calculation
        base_speed = 3.0
        if self.boost_active > 0:
            base_speed *= 2.5

        move_dist = drive * base_speed
        next_x = self.x + math.cos(self.angle) * move_dist
        next_y = self.y + math.sin(self.angle) * move_dist

        # Map Boundary Collisions
        next_x = max(self.radius, min(SCREEN_WIDTH - self.radius, next_x))
        next_y = max(self.radius, min(SCREEN_HEIGHT - self.radius, next_y))

        # Obstacle Collisions
        for obs in obstacles:
            if math.hypot(next_x - obs.x, next_y - obs.y) < (self.radius + obs.radius):
                next_x, next_y = self.x, self.y  # Stop on collision
                break

        self.x, self.y = next_x, next_y

        # Ability Execution
        if want_boost and self.boost_cd == 0:
            self.boost_active = BOOST_DURATION
            self.boost_cd = BOOST_COOLDOWN

        if want_shield and self.shield_cd == 0:
            self.shield_active = SHIELD_DURATION
            self.shield_cd = SHIELD_COOLDOWN

        if want_fire and self.fire_cd == 0:
            bullet_x = self.x + math.cos(self.angle) * (self.radius + 4)
            bullet_y = self.y + math.sin(self.angle) * (self.radius + 4)
            new_bullets.append(Bullet(bullet_x, bullet_y, self.angle, self.team))
            self.fire_cd = MAX_FIRE_COOLDOWN

    def take_damage(self, amount: float):
        if self.shield_active > 0:
            return  # Invulnerable
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    def draw(self, surface):
        if not self.alive:
            return

        color = COLOR_TEAM_A if self.team == 0 else COLOR_TEAM_B

        # Shield Effect
        if self.shield_active > 0:
            pygame.draw.circle(surface, (0, 255, 255), (int(self.x), int(self.y)), int(self.radius + 5), 2)

        # Base Body
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(self.radius))

        # Direction Pointer
        hx = self.x + math.cos(self.angle) * (self.radius + 6)
        hy = self.y + math.sin(self.angle) * (self.radius + 6)
        pygame.draw.line(surface, (255, 255, 255), (self.x, self.y), (hx, hy), 3)


#  Main Sandbox Controller

class Simulation:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("NEAT 2D Tactical Sandbox")
        self.clock = pygame.time.Clock()

        # Generate Map Obstacles
        self.obstacles = [
            Obstacle(300, 200, 45),
            Obstacle(700, 500, 50),
            Obstacle(500, 350, 60),
            Obstacle(200, 500, 40),
            Obstacle(800, 200, 40),
        ]

    def evaluate_generation(self, genomes, config):
        """Runs a batch evaluation episode for a NEAT generation."""
        bots: list[Bot] = []
        bullets: list[Bullet] = []

        # Asymmetric Spawn setup
        # Team 0 (Blue): Top-Left Corner | Team 1 (Red): Bottom-Right Corner
        for i, (g_id, genome) in enumerate(genomes):
            team = 0 if i % 2 == 0 else 1
            if team == 0:
                x = random.uniform(50, 150)
                y = random.uniform(50, 150)
                angle = random.uniform(-0.5, 0.5)
            else:
                x = random.uniform(SCREEN_WIDTH - 150, SCREEN_WIDTH - 50)
                y = random.uniform(SCREEN_HEIGHT - 150, SCREEN_HEIGHT - 50)
                angle = math.pi + random.uniform(-0.5, 0.5)

            bots.append(Bot(x, y, angle, team, genome))

        # Episode Loop (Max 600 frames = 10s simulation window per generation)
        for frame in range(600):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            # 1. Update Bullets
            for b in bullets:
                if b.alive:
                    b.update(self.obstacles)

            # 2. Update Bots
            active_teams = set()
            for bot in bots:
                if not bot.alive:
                    continue

                active_teams.add(bot.team)
                sensors = bot.get_sensors(bots, self.obstacles, bullets)
                outputs = bot.brain.activate(sensors)
                bot.update(outputs, bullets, self.obstacles)

            # 3. Bullet vs Bot Hit Detection
            for b in bullets:
                if not b.alive:
                    continue
                for bot in bots:
                    if bot.alive and bot.team != b.owner_team:
                        if math.hypot(b.x - bot.x, b.y - bot.y) <= (b.radius + bot.radius):
                            bot.take_damage(35.0)
                            b.alive = False
                            # Credit owner genome for damage dealt
                            break

            bullets = [b for b in bullets if b.alive]

            # Stop early if one team is completely wiped out
            if len(active_teams) <= 1:
                break

            # Rendering Phase
            self.screen.fill(COLOR_BG)
            for obs in self.obstacles:
                obs.draw(self.screen)
            for b in bullets:
                b.draw(self.screen)
            for bot in bots:
                bot.draw(self.screen)

            pygame.display.flip()
            self.clock.tick(FPS)

        # Fitness Assignment
        for bot in bots:
            # Reward dealing damage, surviving longer, and maintaining remaining HP
            bot.brain.fitness = (bot.survival_time * 0.1) + (bot.hp * 0.5) + bot.damage_dealt


def main():
    # override defaultg config
    config = Config()
    config.N_INPUTS = 14
    config.N_OUTPUTS = 5
    config.POP_SIZE = 20

    sim = Simulation()
    pop = Population(config)

    for gen in range(config.MAX_GENERATIONS):
        # Pair genomes with their evaluation
        genome_pairs = [(i, g) for i, g in enumerate(pop.genomes)]
        sim.evaluate_generation(genome_pairs, config)

        fitnesses = [g.fitness for g in pop.genomes]
        print(f"Gen {gen:3d} | Best Fitness: {max(fitnesses):.2f} | Avg Fitness: {sum(fitnesses)/len(fitnesses):.2f}")

        pop.evolve(fitnesses)


if __name__ == "__main__":
    main()
