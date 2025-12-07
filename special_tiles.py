"""
Special Tile Manager
Handles traps, power-ups, and speed zones in the maze
"""

import random
import time
import math
from OpenGL.GL import *

class SpecialTileManager:
    def __init__(self, maze, maze_size):
        self.maze = maze
        self.maze_size = maze_size

        # Special tiles dictionary: (x, y) -> type
        self.tiles = {}

        # Player state
        self.speed_modifier = 1.0
        self.current_tile = None

        # Hint system
        self.hints_remaining = 3
        self.hint_active = False
        self.hint_start_time = 0
        self.hint_duration = 5.0  # seconds

        # Animation
        self.animation_time = 0

        # Tile types
        self.TRAP_RESET = 'trap_reset'
        self.TRAP_TURN = 'trap_turn'
        self.POWERUP_LAUNCH = 'powerup_launch'
        self.SPEED_SLOW = 'speed_slow'
        self.SPEED_FAST = 'speed_fast'

        # Generate special tiles
        self.generate_tiles()

    def generate_tiles(self):
        """Generate special tiles throughout the maze"""
        self.tiles = {}

        # Get solution path to place speed boosts
        from maze_generator import MazeGenerator
        gen = MazeGenerator(self.maze_size)
        gen.maze = self.maze
        solution_path = gen.get_solution_path()

        # Place speed boosts on main path (every few cells)
        for i, (x, y) in enumerate(solution_path):
            if i > 0 and i < len(solution_path) - 1 and i % 4 == 0:
                self.tiles[(x, y)] = self.SPEED_FAST

        # Find dead ends for traps
        dead_ends = self.find_dead_ends()

        # Place reset traps in some dead ends
        for x, y in random.sample(dead_ends, min(len(dead_ends) // 3, 5)):
            if (x, y) not in self.tiles:
                self.tiles[(x, y)] = self.TRAP_RESET

        # Place turn traps in some dead ends
        for x, y in random.sample(dead_ends, min(len(dead_ends) // 3, 3)):
            if (x, y) not in self.tiles:
                self.tiles[(x, y)] = self.TRAP_TURN

        # Place slow zones off the main path
        slow_count = 0
        for y in range(self.maze_size):
            for x in range(self.maze_size):
                if (x, y) not in self.tiles and (x, y) not in solution_path:
                    if random.random() < 0.1 and slow_count < 15:
                        self.tiles[(x, y)] = self.SPEED_SLOW
                        slow_count += 1

        # Place a few launch pads
        launch_positions = random.sample(
            [(x, y) for y in range(self.maze_size) for x in range(self.maze_size)
             if (x, y) not in self.tiles and (x, y) not in [(0, 0), (self.maze_size-1, self.maze_size-1)]],
            min(3, self.maze_size * self.maze_size // 10)
        )
        for x, y in launch_positions:
            self.tiles[(x, y)] = self.POWERUP_LAUNCH

    def find_dead_ends(self):
        """Find all dead end cells in the maze"""
        dead_ends = []

        for y in range(self.maze_size):
            for x in range(self.maze_size):
                # Count walls
                cell = self.maze[y][x]
                wall_count = sum([cell['N'], cell['E'], cell['S'], cell['W']])

                # Dead end has 3 walls
                if wall_count == 3:
                    dead_ends.append((x, y))

        return dead_ends

    def check_tile(self, x, y):
        """
        Check if player is on a special tile and return effect
        Returns effect dict or None
        """
        # Reset speed modifier by default
        self.speed_modifier = 1.0

        if (x, y) in self.tiles:
            tile_type = self.tiles[(x, y)]

            # Only trigger once per tile entry
            if self.current_tile != (x, y):
                self.current_tile = (x, y)

                if tile_type == self.TRAP_RESET:
                    return {'type': 'trap_reset'}
                elif tile_type == self.TRAP_TURN:
                    return {'type': 'trap_turn'}
                elif tile_type == self.POWERUP_LAUNCH:
                    return {'type': 'powerup_launch'}

            # Speed modifiers are continuous
            if tile_type == self.SPEED_SLOW:
                self.speed_modifier = 0.4
                return {'type': 'speed_slow'}
            elif tile_type == self.SPEED_FAST:
                self.speed_modifier = 1.8
                return {'type': 'speed_fast'}
        else:
            self.current_tile = None

        return None

    def reset_effects(self):
        """Reset all temporary effects"""
        self.speed_modifier = 1.0
        self.current_tile = None

    def use_hint(self):
        """Activate hint system (shows solution path)"""
        if self.hints_remaining > 0 and not self.hint_active:
            self.hints_remaining -= 1
            self.hint_active = True
            self.hint_start_time = time.time()
            print(f"Hint activated! ({self.hints_remaining} remaining)")

    def update(self, dt):
        """Update tile animations and effects"""
        self.animation_time += dt

        # Check hint timeout
        if self.hint_active:
            if time.time() - self.hint_start_time > self.hint_duration:
                self.hint_active = False
                print("Hint expired!")

    def render(self, camera):
        """Render special tile effects"""
        glDisable(GL_LIGHTING)

        for (x, y), tile_type in self.tiles.items():
            # Animate tiles
            pulse = 0.5 + 0.5 * math.sin(self.animation_time * 3)

            # Set color based on type - bright and visible
            if tile_type == self.TRAP_RESET:
                color = (1.0, 0.2, 0.2, 0.7 * pulse)  # Bright Red
            elif tile_type == self.TRAP_TURN:
                color = (0.9, 0.2, 0.9, 0.7 * pulse)  # Bright Purple
            elif tile_type == self.POWERUP_LAUNCH:
                color = (1.0, 0.9, 0.2, 0.8 * pulse)  # Bright Yellow
            elif tile_type == self.SPEED_SLOW:
                color = (0.3, 0.5, 1.0, 0.5 * pulse)  # Bright Blue
            elif tile_type == self.SPEED_FAST:
                color = (0.0, 1.0, 1.0, 0.8 * pulse)  # Cyan - stands out!
            else:
                continue

            # Draw colored quad on floor
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

            glColor4f(*color)
            glBegin(GL_QUADS)
            glVertex3f(x, 0.01, y)
            glVertex3f(x + 1, 0.01, y)
            glVertex3f(x + 1, 0.01, y + 1)
            glVertex3f(x, 0.01, y + 1)
            glEnd()

            glDisable(GL_BLEND)

        # Render hint path if active
        if self.hint_active:
            self.render_hint_path()

        glEnable(GL_LIGHTING)

    def render_hint_path(self):
        """Render the solution path as a hint"""
        from maze_generator import MazeGenerator
        gen = MazeGenerator(self.maze_size)
        gen.maze = self.maze
        solution_path = gen.get_solution_path()

        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Draw glowing path
        pulse = 0.3 + 0.3 * math.sin(self.animation_time * 5)
        glColor4f(1.0, 0.5, 0.0, 0.5 * pulse)  # Orange glow

        for x, y in solution_path:
            glBegin(GL_QUADS)
            glVertex3f(x + 0.2, 0.02, y + 0.2)
            glVertex3f(x + 0.8, 0.02, y + 0.2)
            glVertex3f(x + 0.8, 0.02, y + 0.8)
            glVertex3f(x + 0.2, 0.02, y + 0.8)
            glEnd()

        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)

    def get_tile_color(self, x, y):
        """Get the color of a tile for rendering"""
        if (x, y) in self.tiles:
            tile_type = self.tiles[(x, y)]
            if tile_type == self.TRAP_RESET:
                return (1.0, 0.2, 0.2)
            elif tile_type == self.TRAP_TURN:
                return (0.9, 0.2, 0.9)
            elif tile_type == self.POWERUP_LAUNCH:
                return (1.0, 0.9, 0.2)
            elif tile_type == self.SPEED_SLOW:
                return (0.3, 0.5, 1.0)
            elif tile_type == self.SPEED_FAST:
                return (0.0, 1.0, 1.0)  # Cyan
        return None
