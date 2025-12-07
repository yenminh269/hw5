#!/usr/bin/env python3
"""
COSC 4370 Homework #5
Interactive 3D Maze Game with FPS Controls

Features:
- 15x15 maze with recursive backtracking generation
- WASD movement with mouse look (FPS controls)
- Collision detection with walls
- Special tiles: traps, speed zones, launch pads
- Hint system showing solution path
- Timer and position display
- Reset (R) and regenerate maze (N) functionality

Controls:
  W/A/S/D - Move forward/left/backward/right
  Mouse   - Look around
  R       - Reset to entrance
  N       - Generate new maze
  H       - Use hint (3 available)
  P       - Pause/unpause
  ESC     - Quit
"""

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import random
import time
import math
from collections import deque


# =============================================================================
# MAZE GENERATOR
# =============================================================================

class MazeGenerator:
    """Maze Generator using Recursive Backtracking Algorithm"""

    def __init__(self, size):
        self.size = size
        self.maze = None

    def generate(self):
        """Generate a new random maze using recursive backtracking"""
        self.maze = [[{'N': True, 'E': True, 'S': True, 'W': True, 'visited': False}
                      for _ in range(self.size)] for _ in range(self.size)]

        self._carve_path(0, 0)

        for row in self.maze:
            for cell in row:
                cell['visited'] = False

        self.maze[0][0]['N'] = False
        self.maze[self.size-1][self.size-1]['S'] = False

        return self.maze

    def _carve_path(self, x, y):
        """Recursively carve paths through the maze"""
        self.maze[y][x]['visited'] = True

        directions = [
            (0, -1, 'N', 'S'),
            (1, 0, 'E', 'W'),
            (0, 1, 'S', 'N'),
            (-1, 0, 'W', 'E')
        ]

        random.shuffle(directions)

        for dx, dy, direction, opposite in directions:
            nx, ny = x + dx, y + dy

            if (0 <= nx < self.size and 0 <= ny < self.size and
                not self.maze[ny][nx]['visited']):

                self.maze[y][x][direction] = False
                self.maze[ny][nx][opposite] = False
                self._carve_path(nx, ny)

    def get_solution_path(self):
        """Find the solution path from start to end using BFS"""
        start = (0, 0)
        end = (self.size - 1, self.size - 1)

        for row in self.maze:
            for cell in row:
                cell['visited'] = False

        queue = deque([start])
        parent = {start: None}
        self.maze[0][0]['visited'] = True

        while queue:
            x, y = queue.popleft()

            if (x, y) == end:
                path = []
                current = end
                while current is not None:
                    path.append(current)
                    current = parent[current]
                return list(reversed(path))

            directions = [
                (0, -1, 'N'),
                (1, 0, 'E'),
                (0, 1, 'S'),
                (-1, 0, 'W')
            ]

            for dx, dy, direction in directions:
                nx, ny = x + dx, y + dy

                if (0 <= nx < self.size and 0 <= ny < self.size and
                    not self.maze[ny][nx]['visited'] and
                    not self.maze[y][x][direction]):

                    self.maze[ny][nx]['visited'] = True
                    parent[(nx, ny)] = (x, y)
                    queue.append((nx, ny))

        for row in self.maze:
            for cell in row:
                cell['visited'] = False

        return []


# =============================================================================
# FPS CAMERA
# =============================================================================

class FPSCamera:
    """First-Person Camera Controller with Mouse Look and Collision Detection"""

    def __init__(self, x, z, y, maze_size):
        self.x = x
        self.y = y
        self.z = z
        self.maze_size = maze_size

        self.initial_x = x
        self.initial_z = z

        self.yaw = -90
        self.pitch = 0

        self.base_speed = 3.0
        self.speed_modifier = 1.0
        self.mouse_sensitivity = 0.2

        self.radius = 0.2

        self.is_launched = False
        self.launch_height = 0
        self.launch_velocity = 0

        self.ground_height = 0.5

    def reset_position(self, x, z):
        """Reset camera to specified position"""
        self.x = x
        self.z = z
        self.y = self.ground_height
        self.yaw = 0
        self.pitch = 0
        self.is_launched = False
        self.launch_height = 0
        self.speed_modifier = 1.0

    def rotate(self, dx, dy):
        """Rotate camera based on mouse movement"""
        self.yaw -= dx * self.mouse_sensitivity
        self.pitch += dy * self.mouse_sensitivity
        self.pitch = max(-89, min(89, self.pitch))

    def move(self, move_x, move_z, dt, maze):
        """Move camera with collision detection"""
        if self.is_launched:
            self.update_launch(dt)
            return

        yaw_rad = math.radians(self.yaw)

        forward_x = -math.sin(yaw_rad) * move_z
        forward_z = -math.cos(yaw_rad) * move_z

        strafe_x = math.sin(yaw_rad + math.pi/2) * move_x
        strafe_z = math.cos(yaw_rad + math.pi/2) * move_x

        dx = (forward_x + strafe_x) * self.base_speed * self.speed_modifier * dt
        dz = (forward_z + strafe_z) * self.base_speed * self.speed_modifier * dt

        new_x = self.x + dx
        new_z = self.z + dz

        if not self.check_collision(new_x, self.z, maze):
            self.x = new_x

        if not self.check_collision(self.x, new_z, maze):
            self.z = new_z

    def check_collision(self, x, z, maze):
        """Check if position collides with walls"""
        if x < 0 or x >= self.maze_size or z < 0 or z >= self.maze_size:
            return True

        cell_x = int(x)
        cell_y = int(z)

        if not (0 <= cell_x < self.maze_size and 0 <= cell_y < self.maze_size):
            return True

        cell = maze[cell_y][cell_x]

        local_x = x - cell_x
        local_z = z - cell_y

        if cell['N'] and local_z < self.radius:
            return True
        if cell['S'] and local_z > 1 - self.radius:
            return True
        if cell['W'] and local_x < self.radius:
            return True
        if cell['E'] and local_x > 1 - self.radius:
            return True

        return False

    def launch(self):
        """Launch player into the air for bird's eye view"""
        if not self.is_launched:
            self.is_launched = True
            self.launch_velocity = 12.0

    def update_launch(self, dt):
        """Update launch physics"""
        gravity = 15.0

        self.launch_velocity -= gravity * dt
        self.launch_height += self.launch_velocity * dt

        self.y = self.ground_height + self.launch_height

        if self.launch_height <= 0:
            self.launch_height = 0
            self.y = self.ground_height
            self.is_launched = False
            self.launch_velocity = 0

    def apply(self):
        """Apply camera transformation to OpenGL"""
        glLoadIdentity()
        glRotatef(self.pitch, 1, 0, 0)
        glRotatef(-self.yaw, 0, 1, 0)
        glTranslatef(-self.x, -self.y, -self.z)


# =============================================================================
# MAZE RENDERER
# =============================================================================

class MazeRenderer:
    """Handles 3D rendering of maze walls, floor, and ceiling with textures"""

    def __init__(self, maze, maze_size):
        self.maze = maze
        self.maze_size = maze_size
        self.wall_height = 1.0

        self.wall_texture = self.create_brick_texture()
        self.floor_texture = self.create_floor_texture()
        self.ceiling_texture = self.create_ceiling_texture()

        self.wall_colors = {}
        for y in range(maze_size):
            for x in range(maze_size):
                brightness = 0.85 + random.random() * 0.15
                self.wall_colors[(x, y)] = (brightness * 0.7, brightness, brightness * 0.6)

        self.walls_display_list = None
        self.create_walls_display_list()

    def create_brick_texture(self):
        """Create a procedural hedge texture for garden maze walls"""
        width, height = 128, 128
        surface = pygame.Surface((width, height))

        base_green = (50, 130, 50)
        surface.fill(base_green)

        for _ in range(350):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            shade = random.randint(-30, 40)
            leaf_color = (
                max(30, min(100, 55 + shade)),
                max(100, min(180, 140 + shade)),
                max(30, min(90, 50 + shade))
            )
            size = random.randint(4, 10)
            pygame.draw.circle(surface, leaf_color, (x, y), size)

        for _ in range(30):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            dark_color = (35, 80, 35)
            pygame.draw.circle(surface, dark_color, (x, y), random.randint(3, 6))

        for _ in range(120):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            light_color = (80, 170, 70)
            pygame.draw.circle(surface, light_color, (x, y), random.randint(2, 5))

        return self.load_texture_from_surface(surface)

    def create_floor_texture(self):
        """Create a procedural dirt/stone path texture"""
        width, height = 128, 128
        surface = pygame.Surface((width, height))

        base_color = (180, 160, 130)
        surface.fill(base_color)

        for _ in range(400):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            shade = random.randint(-30, 30)
            dirt_color = (
                max(130, min(210, 175 + shade)),
                max(120, min(190, 155 + shade)),
                max(90, min(160, 125 + shade))
            )
            size = random.randint(2, 5)
            pygame.draw.circle(surface, dirt_color, (x, y), size)

        for _ in range(60):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            dark_color = (140, 120, 90)
            pygame.draw.circle(surface, dark_color, (x, y), random.randint(3, 6))

        for _ in range(50):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            light_color = (200, 185, 160)
            pygame.draw.circle(surface, light_color, (x, y), random.randint(2, 4))

        return self.load_texture_from_surface(surface)

    def create_ceiling_texture(self):
        """Create a simple ceiling texture"""
        width, height = 64, 64
        surface = pygame.Surface((width, height))

        base_color = (40, 40, 50)

        for y in range(height):
            for x in range(width):
                variation = random.randint(-10, 10)
                color = tuple(max(0, min(255, c + variation)) for c in base_color)
                surface.set_at((x, y), color)

        return self.load_texture_from_surface(surface)

    def load_texture_from_surface(self, surface):
        """Convert pygame surface to OpenGL texture"""
        texture_data = pygame.image.tostring(surface, "RGB", 1)
        width = surface.get_width()
        height = surface.get_height()

        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)

        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0,
                     GL_RGB, GL_UNSIGNED_BYTE, texture_data)

        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

        return texture_id

    def create_walls_display_list(self):
        """Create a display list for walls to improve performance"""
        self.walls_display_list = glGenLists(1)
        glNewList(self.walls_display_list, GL_COMPILE)

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.wall_texture)

        for y in range(self.maze_size):
            for x in range(self.maze_size):
                cell = self.maze[y][x]
                color = self.wall_colors[(x, y)]
                glColor3f(*color)

                if cell['N']:
                    self.draw_wall(x, y, x + 1, y, 'N')
                if cell['E']:
                    self.draw_wall(x + 1, y, x + 1, y + 1, 'E')
                if cell['S']:
                    self.draw_wall(x + 1, y + 1, x, y + 1, 'S')
                if cell['W']:
                    self.draw_wall(x, y + 1, x, y, 'W')

        glDisable(GL_TEXTURE_2D)
        glEndList()

    def render(self):
        """Render the entire maze"""
        self.render_floor()

        if self.walls_display_list:
            glCallList(self.walls_display_list)
        else:
            self.render_walls()

    def render_floor(self):
        """Render the floor plane"""
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.floor_texture)

        glColor3f(0.8, 0.8, 0.8)

        glBegin(GL_QUADS)
        glNormal3f(0, 1, 0)
        glTexCoord2f(0, 0)
        glVertex3f(0, 0, 0)
        glTexCoord2f(self.maze_size, 0)
        glVertex3f(self.maze_size, 0, 0)
        glTexCoord2f(self.maze_size, self.maze_size)
        glVertex3f(self.maze_size, 0, self.maze_size)
        glTexCoord2f(0, self.maze_size)
        glVertex3f(0, 0, self.maze_size)
        glEnd()

        glDisable(GL_TEXTURE_2D)

    def render_walls(self):
        """Render all maze walls"""
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.wall_texture)

        for y in range(self.maze_size):
            for x in range(self.maze_size):
                cell = self.maze[y][x]
                color = self.wall_colors[(x, y)]
                glColor3f(*color)

                if cell['N']:
                    self.draw_wall(x, y, x + 1, y, 'N')
                if cell['E']:
                    self.draw_wall(x + 1, y, x + 1, y + 1, 'E')
                if cell['S']:
                    self.draw_wall(x + 1, y + 1, x, y + 1, 'S')
                if cell['W']:
                    self.draw_wall(x, y + 1, x, y, 'W')

        glDisable(GL_TEXTURE_2D)

    def draw_wall(self, x1, z1, x2, z2, direction):
        """Draw a thick 3D wall segment"""
        thickness = 0.08

        if direction == 'N':
            self.draw_wall_box(x1, z1 - thickness/2, x2, z1 + thickness/2)
        elif direction == 'S':
            self.draw_wall_box(x2, z2 - thickness/2, x1, z2 + thickness/2)
        elif direction == 'E':
            self.draw_wall_box(x1 - thickness/2, z1, x1 + thickness/2, z2)
        elif direction == 'W':
            self.draw_wall_box(x1 - thickness/2, z2, x1 + thickness/2, z1)

    def draw_wall_box(self, x1, z1, x2, z2):
        """Draw a 3D box for wall with all faces"""
        h = self.wall_height

        min_x, max_x = min(x1, x2), max(x1, x2)
        min_z, max_z = min(z1, z2), max(z1, z2)

        glBegin(GL_QUADS)
        glNormal3f(0, 0, -1)
        glTexCoord2f(0, 0); glVertex3f(min_x, 0, min_z)
        glTexCoord2f(1, 0); glVertex3f(max_x, 0, min_z)
        glTexCoord2f(1, 1); glVertex3f(max_x, h, min_z)
        glTexCoord2f(0, 1); glVertex3f(min_x, h, min_z)
        glEnd()

        glBegin(GL_QUADS)
        glNormal3f(0, 0, 1)
        glTexCoord2f(0, 0); glVertex3f(max_x, 0, max_z)
        glTexCoord2f(1, 0); glVertex3f(min_x, 0, max_z)
        glTexCoord2f(1, 1); glVertex3f(min_x, h, max_z)
        glTexCoord2f(0, 1); glVertex3f(max_x, h, max_z)
        glEnd()

        glBegin(GL_QUADS)
        glNormal3f(-1, 0, 0)
        glTexCoord2f(0, 0); glVertex3f(min_x, 0, max_z)
        glTexCoord2f(1, 0); glVertex3f(min_x, 0, min_z)
        glTexCoord2f(1, 1); glVertex3f(min_x, h, min_z)
        glTexCoord2f(0, 1); glVertex3f(min_x, h, max_z)
        glEnd()

        glBegin(GL_QUADS)
        glNormal3f(1, 0, 0)
        glTexCoord2f(0, 0); glVertex3f(max_x, 0, min_z)
        glTexCoord2f(1, 0); glVertex3f(max_x, 0, max_z)
        glTexCoord2f(1, 1); glVertex3f(max_x, h, max_z)
        glTexCoord2f(0, 1); glVertex3f(max_x, h, min_z)
        glEnd()

        glBegin(GL_QUADS)
        glNormal3f(0, 1, 0)
        glTexCoord2f(0, 0); glVertex3f(min_x, h, min_z)
        glTexCoord2f(1, 0); glVertex3f(max_x, h, min_z)
        glTexCoord2f(1, 1); glVertex3f(max_x, h, max_z)
        glTexCoord2f(0, 1); glVertex3f(min_x, h, max_z)
        glEnd()


# =============================================================================
# SPECIAL TILE MANAGER
# =============================================================================

class SpecialTileManager:
    """Handles traps, power-ups, and speed zones in the maze"""

    def __init__(self, maze, maze_size):
        self.maze = maze
        self.maze_size = maze_size

        self.tiles = {}

        self.speed_modifier = 1.0
        self.current_tile = None

        self.hints_remaining = 3
        self.hint_active = False
        self.hint_start_time = 0
        self.hint_duration = 5.0

        self.animation_time = 0

        self.TRAP_RESET = 'trap_reset'
        self.TRAP_TURN = 'trap_turn'
        self.POWERUP_LAUNCH = 'powerup_launch'
        self.SPEED_SLOW = 'speed_slow'
        self.SPEED_FAST = 'speed_fast'

        self.generate_tiles()

    def generate_tiles(self):
        """Generate special tiles throughout the maze"""
        self.tiles = {}

        gen = MazeGenerator(self.maze_size)
        gen.maze = self.maze
        solution_path = gen.get_solution_path()

        for i, (x, y) in enumerate(solution_path):
            if i > 0 and i < len(solution_path) - 1 and i % 4 == 0:
                self.tiles[(x, y)] = self.SPEED_FAST

        dead_ends = self.find_dead_ends()

        for x, y in random.sample(dead_ends, min(len(dead_ends) // 3, 5)):
            if (x, y) not in self.tiles:
                self.tiles[(x, y)] = self.TRAP_RESET

        for x, y in random.sample(dead_ends, min(len(dead_ends) // 3, 3)):
            if (x, y) not in self.tiles:
                self.tiles[(x, y)] = self.TRAP_TURN

        slow_count = 0
        for y in range(self.maze_size):
            for x in range(self.maze_size):
                if (x, y) not in self.tiles and (x, y) not in solution_path:
                    if random.random() < 0.1 and slow_count < 15:
                        self.tiles[(x, y)] = self.SPEED_SLOW
                        slow_count += 1

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
                cell = self.maze[y][x]
                wall_count = sum([cell['N'], cell['E'], cell['S'], cell['W']])

                if wall_count == 3:
                    dead_ends.append((x, y))

        return dead_ends

    def check_tile(self, x, y):
        """Check if player is on a special tile and return effect"""
        self.speed_modifier = 1.0

        if (x, y) in self.tiles:
            tile_type = self.tiles[(x, y)]

            if self.current_tile != (x, y):
                self.current_tile = (x, y)

                if tile_type == self.TRAP_RESET:
                    return {'type': 'trap_reset'}
                elif tile_type == self.TRAP_TURN:
                    return {'type': 'trap_turn'}
                elif tile_type == self.POWERUP_LAUNCH:
                    return {'type': 'powerup_launch'}

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

    def update(self, dt):
        """Update tile animations and effects"""
        self.animation_time += dt

        if self.hint_active:
            if time.time() - self.hint_start_time > self.hint_duration:
                self.hint_active = False

    def render(self, camera):
        """Render special tile effects"""
        glDisable(GL_LIGHTING)

        for (x, y), tile_type in self.tiles.items():
            pulse = 0.5 + 0.5 * math.sin(self.animation_time * 3)

            if tile_type == self.TRAP_RESET:
                color = (1.0, 0.2, 0.2, 0.7 * pulse)
            elif tile_type == self.TRAP_TURN:
                color = (0.9, 0.2, 0.9, 0.7 * pulse)
            elif tile_type == self.POWERUP_LAUNCH:
                color = (1.0, 0.9, 0.2, 0.8 * pulse)
            elif tile_type == self.SPEED_SLOW:
                color = (0.3, 0.5, 1.0, 0.5 * pulse)
            elif tile_type == self.SPEED_FAST:
                color = (0.0, 1.0, 1.0, 0.8 * pulse)
            else:
                continue

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

        if self.hint_active:
            self.render_hint_path()

        glEnable(GL_LIGHTING)

    def render_hint_path(self):
        """Render the solution path as a hint"""
        gen = MazeGenerator(self.maze_size)
        gen.maze = self.maze
        solution_path = gen.get_solution_path()

        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        pulse = 0.3 + 0.3 * math.sin(self.animation_time * 5)
        glColor4f(1.0, 0.5, 0.0, 0.5 * pulse)

        for x, y in solution_path:
            glBegin(GL_QUADS)
            glVertex3f(x + 0.2, 0.02, y + 0.2)
            glVertex3f(x + 0.8, 0.02, y + 0.2)
            glVertex3f(x + 0.8, 0.02, y + 0.8)
            glVertex3f(x + 0.2, 0.02, y + 0.8)
            glEnd()

        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)


# =============================================================================
# MAIN GAME CLASS
# =============================================================================

class MazeGame:
    def __init__(self, maze_size=15):
        pygame.init()
        self.display = (1200, 800)
        self.screen = pygame.display.set_mode(self.display, DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Garden Hedge Maze - COSC 4370 HW5")

        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

        self.display_center = [self.display[i] // 2 for i in range(2)]
        pygame.mouse.set_pos(self.display_center)

        self.maze_size = maze_size

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 18)

        self.setup_opengl()

        self.maze_generator = MazeGenerator(maze_size)
        self.maze = None
        self.camera = None
        self.renderer = None
        self.special_tiles = None

        self.start_time = None
        self.elapsed_time = 0
        self.running = True
        self.paused = False
        self.game_won = False
        self.win_time = 0

        self.notifications = []
        self.large_font = pygame.font.SysFont("Arial", 32, bold=True)
        self.title_font = pygame.font.SysFont("Arial", 64, bold=True)

        self.mouse_sensitivity = 0.2

        self.generate_new_maze()

        self.show_notification("Navigate to the GREEN goal! Press H for hints", (200, 255, 200), 4.0, large=True)

    def setup_opengl(self):
        """Configure OpenGL settings"""
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        glClearColor(0.53, 0.81, 0.98, 1.0)

        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.5, 0.5, 0.45, 1])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 0.98, 0.9, 1])
        glLightfv(GL_LIGHT0, GL_POSITION, [1, 10, 1, 0])

        glEnable(GL_LIGHT1)
        glLightfv(GL_LIGHT1, GL_AMBIENT, [0.35, 0.4, 0.45, 1])
        glLightfv(GL_LIGHT1, GL_DIFFUSE, [0.6, 0.65, 0.7, 1])

        glMatrixMode(GL_PROJECTION)
        gluPerspective(70, (self.display[0] / self.display[1]), 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

        glDisable(GL_FOG)

    def generate_new_maze(self):
        """Generate a new random maze"""
        self.maze = self.maze_generator.generate()

        start_x, start_y = 0.5, 0.5

        self.camera = FPSCamera(start_x, start_y, 0.5, self.maze_size)

        self.renderer = MazeRenderer(self.maze, self.maze_size)

        self.special_tiles = SpecialTileManager(self.maze, self.maze_size)

        self.start_time = time.time()
        self.elapsed_time = 0
        self.game_won = False
        self.notifications = []

    def reset_position(self):
        """Reset player to start position without regenerating maze"""
        self.camera.reset_position(0.5, 0.5)
        self.start_time = time.time()
        self.elapsed_time = 0
        self.special_tiles.reset_effects()
        self.game_won = False
        self.notifications = []

    def show_notification(self, text, color=(255, 255, 255), duration=2.0, large=False):
        """Add an on-screen notification message"""
        self.notifications = [{
            'text': text,
            'color': color,
            'expire_time': time.time() + duration,
            'large': large
        }]

    def handle_events(self):
        """Handle keyboard and mouse events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r:
                    self.reset_position()
                    self.show_notification("Position Reset!", (255, 200, 100), 2.0, large=True)
                elif event.key == pygame.K_n:
                    self.generate_new_maze()
                    self.show_notification("New Maze Generated!", (100, 255, 200), 2.0, large=True)
                elif event.key == pygame.K_h:
                    if self.special_tiles.hints_remaining > 0:
                        self.special_tiles.use_hint()
                        self.show_notification(f"Hint Activated! ({self.special_tiles.hints_remaining} left)", (255, 150, 50), 2.0)
                    else:
                        self.show_notification("No hints remaining!", (255, 100, 100), 1.5)
                elif event.key == pygame.K_p:
                    self.paused = not self.paused
                    if not self.paused:
                        pygame.mouse.set_pos(self.display_center)
                elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                    self.mouse_sensitivity = min(0.5, self.mouse_sensitivity + 0.05)
                    self.camera.mouse_sensitivity = self.mouse_sensitivity
                    self.show_notification(f"Sensitivity: {self.mouse_sensitivity:.2f}", (200, 200, 255), 1.0)
                elif event.key == pygame.K_MINUS:
                    self.mouse_sensitivity = max(0.05, self.mouse_sensitivity - 0.05)
                    self.camera.mouse_sensitivity = self.mouse_sensitivity
                    self.show_notification(f"Sensitivity: {self.mouse_sensitivity:.2f}", (200, 200, 255), 1.0)

            if event.type == pygame.MOUSEMOTION and not self.paused:
                mouse_move = [event.pos[i] - self.display_center[i] for i in range(2)]
                if mouse_move[0] != 0 or mouse_move[1] != 0:
                    self.camera.rotate(mouse_move[0], mouse_move[1])

        if not self.paused:
            pygame.mouse.set_pos(self.display_center)

    def update(self, dt):
        """Update game state"""
        if self.paused:
            return

        self.elapsed_time = time.time() - self.start_time

        self.camera.update_launch(dt)

        keys = pygame.key.get_pressed()

        move_x, move_z = 0, 0
        if keys[K_w]:
            move_z = 1
        if keys[K_s]:
            move_z = -1
        if keys[K_a]:
            move_x = -1
        if keys[K_d]:
            move_x = 1

        if move_x != 0 or move_z != 0:
            self.camera.move(move_x, move_z, dt, self.maze)

        cell_x = int(self.camera.x)
        cell_y = int(self.camera.z)

        if 0 <= cell_x < self.maze_size and 0 <= cell_y < self.maze_size:
            effect = self.special_tiles.check_tile(cell_x, cell_y)
            if effect:
                self.apply_effect(effect)

        self.special_tiles.update(dt)

        self.camera.speed_modifier = self.special_tiles.speed_modifier

        glLightfv(GL_LIGHT1, GL_POSITION, [self.camera.x, 2, self.camera.z, 1])

        if self.check_win_condition():
            self.handle_win()

    def apply_effect(self, effect):
        """Apply special tile effect to player"""
        if effect['type'] == 'trap_reset':
            self.reset_position()
            self.show_notification("TRAP! Back to Start!", (255, 50, 50), 2.5, large=True)
        elif effect['type'] == 'trap_turn':
            self.camera.yaw += 90
            self.show_notification("DIZZY! Turned 90", (200, 50, 200), 2.0, large=True)
        elif effect['type'] == 'powerup_launch':
            self.camera.launch()
            self.show_notification("LAUNCHED! Look around!", (255, 255, 50), 3.0, large=True)
        elif effect['type'] == 'speed_slow':
            self.show_notification("Slow Zone...", (100, 150, 255), 1.5)
        elif effect['type'] == 'speed_fast':
            self.show_notification("SPEED BOOST!", (0, 255, 255), 1.5)

    def check_win_condition(self):
        """Check if player reached the goal"""
        cell_x = int(self.camera.x)
        cell_y = int(self.camera.z)

        return cell_x == self.maze_size - 1 and cell_y == self.maze_size - 1

    def handle_win(self):
        """Handle winning the maze"""
        self.game_won = True
        self.win_time = self.elapsed_time
        self.paused = True

    def render_win_screen(self):
        """Render the victory screen overlay"""
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.display[0], self.display[1], 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0, 0, 0, 0.7)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(self.display[0], 0)
        glVertex2f(self.display[0], self.display[1])
        glVertex2f(0, self.display[1])
        glEnd()

        pulse = 0.5 + 0.5 * math.sin(time.time() * 3)
        glColor4f(0.2 * pulse, 0.8 * pulse, 0.2 * pulse, 0.8)
        border = 50
        glLineWidth(4)
        glBegin(GL_LINE_LOOP)
        glVertex2f(border, border)
        glVertex2f(self.display[0] - border, border)
        glVertex2f(self.display[0] - border, self.display[1] - border)
        glVertex2f(border, self.display[1] - border)
        glEnd()
        glLineWidth(1)

        glDisable(GL_BLEND)

        center_x = self.display[0] // 2
        center_y = self.display[1] // 2

        title_text = "MAZE COMPLETE!"
        title_surface = self.title_font.render(title_text, True, (50, 255, 50))
        title_x = center_x - title_surface.get_width() // 2
        title_y = center_y - 100

        glow_surface = self.title_font.render(title_text, True, (100, 255, 100))
        self.draw_text_at(glow_surface, title_x - 2, title_y - 2)
        self.draw_text_at(title_surface, title_x, title_y)

        time_text = f"Time: {self.win_time:.2f} seconds"
        time_surface = self.large_font.render(time_text, True, (255, 255, 100))
        time_x = center_x - time_surface.get_width() // 2
        self.draw_text_at(time_surface, time_x, center_y - 20)

        instructions = [
            ("Press N for New Maze", (100, 200, 255)),
            ("Press R to Retry", (255, 200, 100)),
            ("Press ESC to Quit", (200, 200, 200))
        ]
        for i, (text, color) in enumerate(instructions):
            inst_surface = self.font.render(text, True, color)
            inst_x = center_x - inst_surface.get_width() // 2
            self.draw_text_at(inst_surface, inst_x, center_y + 40 + i * 35)

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

    def draw_text_at(self, surface, x, y):
        """Helper to draw a pygame surface at screen position"""
        text_data = pygame.image.tostring(surface, "RGBA", True)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glWindowPos2d(x, self.display[1] - y - surface.get_height())
        glDrawPixels(surface.get_width(), surface.get_height(),
                    GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        glDisable(GL_BLEND)

    def render(self):
        """Render the game"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        self.camera.apply()

        self.renderer.render()

        self.special_tiles.render(self.camera)

        self.render_goal()

        self.render_hud()

        if self.game_won:
            self.render_win_screen()

        pygame.display.flip()

    def render_goal(self):
        """Draw a special marker at the goal location"""
        x, z = self.maze_size - 1, self.maze_size - 1

        glDisable(GL_LIGHTING)

        pulse = 0.5 + 0.5 * abs((time.time() * 2) % 2 - 1)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glColor4f(0, pulse, 0, 0.7)
        glBegin(GL_QUADS)
        glVertex3f(x + 0.1, 0.02, z + 0.1)
        glVertex3f(x + 0.9, 0.02, z + 0.1)
        glVertex3f(x + 0.9, 0.02, z + 0.9)
        glVertex3f(x + 0.1, 0.02, z + 0.9)
        glEnd()

        glColor4f(0, pulse, 0, 0.3)
        glBegin(GL_LINES)
        glVertex3f(x + 0.5, 0, z + 0.5)
        glVertex3f(x + 0.5, 2.0, z + 0.5)
        glEnd()

        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)

    def render_hud(self):
        """Render heads-up display with game info"""
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.display[0], self.display[1], 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glColor4f(0, 0, 0, 0.5)
        glBegin(GL_QUADS)
        glVertex2f(10, 10)
        glVertex2f(250, 10)
        glVertex2f(250, 150)
        glVertex2f(10, 150)
        glEnd()

        cx, cy = self.display[0] // 2, self.display[1] // 2
        glColor4f(1, 1, 1, 0.7)
        glLineWidth(2)
        glBegin(GL_LINES)
        glVertex2f(cx - 10, cy)
        glVertex2f(cx + 10, cy)
        glVertex2f(cx, cy - 10)
        glVertex2f(cx, cy + 10)
        glEnd()
        glLineWidth(1)

        glDisable(GL_BLEND)

        goal_x, goal_z = self.maze_size - 0.5, self.maze_size - 0.5
        distance = math.sqrt((self.camera.x - goal_x)**2 + (self.camera.z - goal_z)**2)

        fps = self.clock.get_fps()
        self.draw_text_optimized(f"FPS: {fps:.1f}", 20, 20, (100, 255, 100))
        self.draw_text_optimized(f"Time: {self.elapsed_time:.1f}s", 20, 45, (255, 255, 255))
        self.draw_text_optimized(f"Position: ({int(self.camera.x)}, {int(self.camera.z)})", 20, 70, (255, 200, 100))
        self.draw_text_optimized(f"Distance: {distance:.1f}", 20, 95, (100, 255, 100) if distance < 5 else (255, 255, 255))
        self.draw_text_optimized(f"Hints: {self.special_tiles.hints_remaining}", 20, 120, (255, 255, 255))

        if self.special_tiles.speed_modifier != 1.0:
            speed_text = "FAST!" if self.special_tiles.speed_modifier > 1.0 else "SLOW"
            color = (0, 255, 0) if self.special_tiles.speed_modifier > 1.0 else (255, 128, 0)
            self.draw_text_optimized(speed_text, 20, 120, color)

        if self.camera.is_launched:
            self.draw_text_optimized("AIRBORNE!", 20, 145, (255, 255, 0))
            self.render_minimap()

        self.render_notifications()

        if self.paused:
            self.draw_text_optimized("PAUSED - Press P to continue", self.display[0]//2 - 150, self.display[1] - 50, color=(255, 255, 0))

        controls = [
            "WASD: Move | Mouse: Look | +/-: Sensitivity",
            "R: Reset | N: New Maze | H: Hint | P: Pause"
        ]
        for i, ctrl in enumerate(controls):
            self.draw_text_optimized(ctrl, self.display[0] - 420, self.display[1] - 60 + i*25, (180, 180, 180))

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

    def render_notifications(self):
        """Render center-screen notification messages"""
        current_time = time.time()

        self.notifications = [n for n in self.notifications if n['expire_time'] > current_time]

        center_x = self.display[0] // 2
        start_y = self.display[1] // 3

        for i, notif in enumerate(self.notifications):
            remaining = notif['expire_time'] - current_time
            alpha = min(1.0, remaining / 0.5)

            font = self.large_font if notif.get('large') else self.font

            color = notif['color']
            faded_color = (
                int(color[0] * alpha),
                int(color[1] * alpha),
                int(color[2] * alpha)
            )

            text_surface = font.render(notif['text'], True, faded_color)
            text_width = text_surface.get_width()

            x = center_x - text_width // 2
            y = start_y + i * 45

            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glColor4f(0, 0, 0, 0.5 * alpha)
            padding = 10
            glBegin(GL_QUADS)
            glVertex2f(x - padding, y - 5)
            glVertex2f(x + text_width + padding, y - 5)
            glVertex2f(x + text_width + padding, y + text_surface.get_height() + 5)
            glVertex2f(x - padding, y + text_surface.get_height() + 5)
            glEnd()
            glDisable(GL_BLEND)

            text_data = pygame.image.tostring(text_surface, "RGBA", True)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glWindowPos2d(x, self.display[1] - y - text_surface.get_height())
            glDrawPixels(text_surface.get_width(), text_surface.get_height(),
                        GL_RGBA, GL_UNSIGNED_BYTE, text_data)
            glDisable(GL_BLEND)

    def draw_text_optimized(self, text, x, y, color=(255, 255, 255)):
        """Draw 2D text on screen"""
        text_surface = self.font.render(text, True, color, (0, 0, 0))
        text_data = pygame.image.tostring(text_surface, "RGBA", True)

        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glWindowPos2d(x, self.display[1] - y - text_surface.get_height())
        glDrawPixels(text_surface.get_width(), text_surface.get_height(),
                     GL_RGBA, GL_UNSIGNED_BYTE, text_data)

        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)

    def render_minimap(self):
        """Render a minimap in the corner when airborne"""
        map_size = 200
        map_x = self.display[0] - map_size - 20
        map_y = 20
        cell_size = map_size / self.maze_size

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glColor4f(0, 0, 0, 0.7)
        glBegin(GL_QUADS)
        glVertex2f(map_x - 5, map_y - 5)
        glVertex2f(map_x + map_size + 5, map_y - 5)
        glVertex2f(map_x + map_size + 5, map_y + map_size + 5)
        glVertex2f(map_x - 5, map_y + map_size + 5)
        glEnd()

        glColor4f(0.6, 0.4, 0.3, 1.0)
        glLineWidth(2)
        for y in range(self.maze_size):
            for x in range(self.maze_size):
                cell = self.maze[y][x]
                cx = map_x + x * cell_size
                cy = map_y + y * cell_size

                glBegin(GL_LINES)
                if cell['N']:
                    glVertex2f(cx, cy)
                    glVertex2f(cx + cell_size, cy)
                if cell['E']:
                    glVertex2f(cx + cell_size, cy)
                    glVertex2f(cx + cell_size, cy + cell_size)
                if cell['S']:
                    glVertex2f(cx, cy + cell_size)
                    glVertex2f(cx + cell_size, cy + cell_size)
                if cell['W']:
                    glVertex2f(cx, cy)
                    glVertex2f(cx, cy + cell_size)
                glEnd()

        for (tx, ty), tile_type in self.special_tiles.tiles.items():
            cx = map_x + tx * cell_size + cell_size/2
            cy = map_y + ty * cell_size + cell_size/2

            if tile_type == 'trap_reset':
                glColor4f(1, 0, 0, 0.8)
            elif tile_type == 'trap_turn':
                glColor4f(0.8, 0, 0.8, 0.8)
            elif tile_type == 'powerup_launch':
                glColor4f(1, 1, 0, 0.8)
            elif tile_type == 'speed_slow':
                glColor4f(0, 0, 1, 0.6)
            elif tile_type == 'speed_fast':
                glColor4f(0, 1, 0, 0.8)
            else:
                continue

            glPointSize(4)
            glBegin(GL_POINTS)
            glVertex2f(cx, cy)
            glEnd()

        goal_x = map_x + (self.maze_size - 0.5) * cell_size
        goal_y = map_y + (self.maze_size - 0.5) * cell_size
        glColor4f(0, 1, 0, 1.0)
        glPointSize(8)
        glBegin(GL_POINTS)
        glVertex2f(goal_x, goal_y)
        glEnd()

        pulse = 0.5 + 0.5 * math.sin(time.time() * 5)
        player_x = map_x + self.camera.x * cell_size
        player_y = map_y + self.camera.z * cell_size
        glColor4f(1, 1, 1, pulse)
        glPointSize(6)
        glBegin(GL_POINTS)
        glVertex2f(player_x, player_y)
        glEnd()

        glPointSize(1)
        glLineWidth(1)
        glDisable(GL_BLEND)

    def run(self):
        """Main game loop"""
        print("\n" + "="*60)
        print("GARDEN HEDGE MAZE - COSC 4370 HW5")
        print("="*60)
        print("\nControls:")
        print("  W/A/S/D - Move")
        print("  Mouse   - Look around")
        print("  R       - Reset to start over at the entrance")
        print("  N       - Restart and re-randomize the maze")
        print("  H       - Use hint (limited)")
        print("  P       - Pause")
        print("  ESC     - Quit")
        print("\nSpecial Tiles:")
        print("  Red     - Trap! Resets position")
        print("  Purple  - Trap! Turns you 90 degrees")
        print("  Green   - Speed boost on main path")
        print("  Yellow  - Launch pad for aerial view")
        print("  Blue    - Slow zone off main path")
        print("\nGoal: Reach the opposite corner!\n")

        while self.running:
            dt = self.clock.tick(60) / 1000.0

            self.handle_events()
            self.update(dt)
            self.render()

        pygame.quit()


def main():
    game = MazeGame(maze_size=15)
    game.run()


if __name__ == '__main__':
    main()
