"""
Maze Renderer
Handles 3D rendering of maze walls, floor, and ceiling with textures
"""

import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
import random

class MazeRenderer:
    def __init__(self, maze, maze_size):
        self.maze = maze
        self.maze_size = maze_size
        self.wall_height = 1.0

        # Generate textures
        self.wall_texture = self.create_brick_texture()
        self.floor_texture = self.create_floor_texture()
        self.ceiling_texture = self.create_ceiling_texture()

        # Color variation for walls
        self.wall_colors = {}
        for y in range(maze_size):
            for x in range(maze_size):
                # Slight color variation
                brightness = 0.8 + random.random() * 0.2
                self.wall_colors[(x, y)] = (brightness, brightness, brightness)

        # Create display lists for performance optimization
        self.walls_display_list = None
        self.create_walls_display_list()

    def create_brick_texture(self):
        """Create a procedural brick texture"""
        width, height = 64, 64
        surface = pygame.Surface((width, height))

        # Base brick color
        brick_color = (150, 80, 60)
        mortar_color = (200, 200, 200)

        surface.fill(mortar_color)

        # Draw bricks
        brick_height = 16
        brick_width = 32

        for row in range(0, height, brick_height):
            offset = brick_width // 2 if (row // brick_height) % 2 else 0
            for col in range(-offset, width, brick_width):
                # Add some color variation
                variation = random.randint(-20, 20)
                color = tuple(max(0, min(255, c + variation)) for c in brick_color)

                pygame.draw.rect(surface, color,
                               (col + 1, row + 1, brick_width - 2, brick_height - 2))

        return self.load_texture_from_surface(surface)

    def create_floor_texture(self):
        """Create a procedural floor texture"""
        width, height = 64, 64
        surface = pygame.Surface((width, height))

        # Checkered pattern
        tile_size = 32
        color1 = (80, 80, 90)
        color2 = (60, 60, 70)

        for y in range(0, height, tile_size):
            for x in range(0, width, tile_size):
                color = color1 if ((x // tile_size) + (y // tile_size)) % 2 == 0 else color2
                pygame.draw.rect(surface, color, (x, y, tile_size, tile_size))

        return self.load_texture_from_surface(surface)

    def create_ceiling_texture(self):
        """Create a simple ceiling texture"""
        width, height = 64, 64
        surface = pygame.Surface((width, height))

        # Dark ceiling with some variation
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
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)

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

                # Render walls for this cell
                if cell['N']:  # North wall
                    self.draw_wall(x, y, x + 1, y, 'N')
                if cell['E']:  # East wall
                    self.draw_wall(x + 1, y, x + 1, y + 1, 'E')
                if cell['S']:  # South wall
                    self.draw_wall(x + 1, y + 1, x, y + 1, 'S')
                if cell['W']:  # West wall
                    self.draw_wall(x, y + 1, x, y, 'W')

        glDisable(GL_TEXTURE_2D)
        glEndList()

    def render(self):
        """Render the entire maze"""
        # Render floor
        self.render_floor()

        # Render ceiling
        self.render_ceiling()

        # Render walls using display list
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

    def render_ceiling(self):
        """Render the ceiling plane"""
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.ceiling_texture)

        glColor3f(0.6, 0.6, 0.6)

        glBegin(GL_QUADS)
        glNormal3f(0, -1, 0)
        glTexCoord2f(0, 0)
        glVertex3f(0, self.wall_height, 0)
        glTexCoord2f(0, self.maze_size)
        glVertex3f(0, self.wall_height, self.maze_size)
        glTexCoord2f(self.maze_size, self.maze_size)
        glVertex3f(self.maze_size, self.wall_height, self.maze_size)
        glTexCoord2f(self.maze_size, 0)
        glVertex3f(self.maze_size, self.wall_height, 0)
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

                # Render walls for this cell
                if cell['N']:  # North wall
                    self.draw_wall(x, y, x + 1, y, 'N')
                if cell['E']:  # East wall
                    self.draw_wall(x + 1, y, x + 1, y + 1, 'E')
                if cell['S']:  # South wall
                    self.draw_wall(x + 1, y + 1, x, y + 1, 'S')
                if cell['W']:  # West wall
                    self.draw_wall(x, y + 1, x, y, 'W')

        glDisable(GL_TEXTURE_2D)

    def draw_wall(self, x1, z1, x2, z2, direction):
        """Draw a single wall segment"""
        # Calculate normal based on direction
        if direction == 'N':
            normal = (0, 0, -1)
        elif direction == 'S':
            normal = (0, 0, 1)
        elif direction == 'E':
            normal = (1, 0, 0)
        elif direction == 'W':
            normal = (-1, 0, 0)
        else:
            normal = (0, 0, 1)

        glBegin(GL_QUADS)
        glNormal3f(*normal)

        # Bottom left
        glTexCoord2f(0, 0)
        glVertex3f(x1, 0, z1)

        # Bottom right
        glTexCoord2f(1, 0)
        glVertex3f(x2, 0, z2)

        # Top right
        glTexCoord2f(1, 1)
        glVertex3f(x2, self.wall_height, z2)

        # Top left
        glTexCoord2f(0, 1)
        glVertex3f(x1, self.wall_height, z1)

        glEnd()

    def highlight_goal(self):
        """Draw a special marker at the goal location"""
        x, y = self.maze_size - 1, self.maze_size - 1

        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)

        # Pulsing green light at goal
        import time
        pulse = 0.5 + 0.5 * abs((time.time() * 2) % 2 - 1)

        glColor3f(0, pulse, 0)

        # Draw a pillar of light
        glBegin(GL_QUADS)
        # Four sides of the pillar
        for angle in [0, 90, 180, 270]:
            import math
            rad = math.radians(angle)
            x_offset = 0.1 * math.cos(rad)
            z_offset = 0.1 * math.sin(rad)

            glVertex3f(x + 0.5 + x_offset, 0, y + 0.5 + z_offset)
            glVertex3f(x + 0.5 + x_offset, self.wall_height * 2, y + 0.5 + z_offset)

        glEnd()

        glEnable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
