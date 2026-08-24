import math
import numpy as np
from config import ARENA_W, ARENA_H, RAY_MAX_DIST, AGENT_RADIUS

class Mapdata:
    """Tracks death gradients across the arena."""
    def __init__(self):
        self.gradients: list[dict] = []  # each: {'x': float, 'y': float, 'strength': float, 'decay': float}
        self.grid_size = 20  # 20x20 pixel cells
        self.grid = np.zeros((ARENA_W // self.grid_size + 1, ARENA_H // self.grid_size + 1))
        self.decay_rate = 0.995  # per frame
        self.max_strength = 10.0

    def add_death(self, x: float, y: float, strength: float = 1.0):
        """Add a death gradient at position."""
        self.gradients.append({
            'x': x,
            'y': y,
            'strength': min(strength, self.max_strength),
            'decay': 0.999  # per frame
        })
        self._update_grid()

    def _update_grid(self):
        """Update the grid for fast lookups."""
        self.grid.fill(0)
        for g in self.gradients:
            if g['strength'] < 0.01:
                continue
            # Apply gradient to grid cells
            gx, gy = int(g['x'] // self.grid_size), int(g['y'] // self.grid_size)
            radius_cells = int(50 // self.grid_size)  # 50 pixel radius

            for dx in range(-radius_cells, radius_cells + 1):
                for dy in range(-radius_cells, radius_cells + 1):
                    cx, cy = gx + dx, gy + dy
                    if 0 <= cx < self.grid.shape[0] and 0 <= cy < self.grid.shape[1]:
                        # Distance in pixels
                        px = cx * self.grid_size + self.grid_size / 2
                        py = cy * self.grid_size + self.grid_size / 2
                        dist = math.hypot(px - g['x'], py - g['y'])
                        if dist < 50:
                            # Gaussian falloff
                            factor = math.exp(-(dist * dist) / (2 * 30 * 30))
                            self.grid[cx, cy] += g['strength'] * factor

    def get_gradient_at(self, x: float, y: float) -> float:
        """Get gradient strength at a point."""
        gx, gy = int(x // self.grid_size), int(y // self.grid_size)
        if 0 <= gx < self.grid.shape[0] and 0 <= gy < self.grid.shape[1]:
            return float(self.grid[gx, gy])
        return 0.0

    def cast_ray(self, agent, dir_x: float, dir_y: float) -> float:
        """Cast a ray through the heatmap."""
        # Sample along ray
        step = 5  # pixels
        max_steps = int(RAY_MAX_DIST / step)
        max_gradient = 0.0
        distance = 0.0

        for i in range(max_steps):
            dist = i * step
            x = agent.x + dir_x * dist
            y = agent.y + dir_y * dist

            if not (0 <= x <= ARENA_W and 0 <= y <= ARENA_H):
                break

            grad = self.get_gradient_at(x, y)
            if grad > max_gradient:
                max_gradient = grad
                distance = dist
                if grad > 0.5:  # found significant gradient
                    break

        # Normalize: return distance to significant gradient, or max
        if max_gradient > 0.1:
            return min(1.0, distance / RAY_MAX_DIST)
        return 1.0  # no gradient in this direction

    def update(self):
        """Decay gradients over time."""
        to_remove = []
        for i, g in enumerate(self.gradients):
            g['strength'] *= g['decay']
            if g['strength'] < 0.01:
                to_remove.append(i)

        for i in reversed(to_remove):
            del self.gradients[i]

        if len(self.gradients) > 100:
            # Keep only strongest gradients
            self.gradients.sort(key=lambda g: g['strength'], reverse=True)
            self.gradients = self.gradients[:100]

        self._update_grid()

    def reset(self):
        """Clear all gradients."""
        self.gradients.clear()
        self.grid.fill(0)
