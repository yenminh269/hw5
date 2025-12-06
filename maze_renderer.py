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
        """Create a procedural brick texture - higher resolution for crisp look"""
        width, height = 128, 128
        surface = pygame.Surface((width, height))

        # Base brick color - warmer tones
        brick_color = (160, 90, 70)
        mortar_color = (180, 175, 165)

        surface.fill(mortar_color)

        # Draw bricks - larger for cleaner look
        brick_height = 32
        brick_width = 64

        for row in range(0, height, brick_height):
            offset = brick_width // 2 if (row // brick_height) % 2 else 0
            for col in range(-offset, width, brick_width):
                # Add some color variation
                variation = random.randint(-15, 15)
                color = tuple(max(0, min(255, c + variation)) for c in brick_color)

                pygame.draw.rect(surface, color,
                               (col + 2, row + 2, brick_width - 4, brick_height - 4))

        return self.load_texture_from_surface(surface)

    def create_floor_texture(self):
        """Create a procedural floor texture - stone tiles"""
        width, height = 128, 128
        surface = pygame.Surface((width, height))

        # Stone tile pattern - cleaner colors
        tile_size = 64
        color1 = (100, 100, 110)
        color2 = (75, 75, 85)
        grout_color = (50, 50, 55)

        surface.fill(grout_color)

        for y in range(0, height, tile_size):
            for x in range(0, width, tile_size):
                color = color1 if ((x // tile_size) + (y // tile_size)) % 2 == 0 else color2
                # Draw tile with grout border
                pygame.draw.rect(surface, color, (x + 2, y + 2, tile_size - 4, tile_size - 4))

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
        """Convert pygame surface to OpenGL texture with crisp filtering"""
        texture_data = pygame.image.tostring(surface, "RGB", 1)
        width = surface.get_width()
        height = surface.get_height()

        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)

        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0,
                     GL_RGB, GL_UNSIGNED_BYTE, texture_data)

        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        # Use GL_NEAREST for crisp, pixel-perfect textures (no blur)
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

        # Ceiling removed to allow aerial view when launched

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
        """Draw a thick 3D wall segment"""
        thickness = 0.08  # Wall thickness

        # Calculate offset based on direction for 3D depth
        if direction == 'N':
            # Wall along X axis at low Z
            self.draw_wall_box(x1, z1 - thickness/2, x2, z1 + thickness/2)
        elif direction == 'S':
            # Wall along X axis at high Z
            self.draw_wall_box(x2, z2 - thickness/2, x1, z2 + thickness/2)
        elif direction == 'E':
            # Wall along Z axis at high X
            self.draw_wall_box(x1 - thickness/2, z1, x1 + thickness/2, z2)
        elif direction == 'W':
            # Wall along Z axis at low X
            self.draw_wall_box(x1 - thickness/2, z2, x1 + thickness/2, z1)

    def draw_wall_box(self, x1, z1, x2, z2):
        """Draw a 3D box for wall with all faces"""
        h = self.wall_height

        # Ensure correct ordering
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_z, max_z = min(z1, z2), max(z1, z2)

        # Front face (facing -Z)
        glBegin(GL_QUADS)
        glNormal3f(0, 0, -1)
        glTexCoord2f(0, 0); glVertex3f(min_x, 0, min_z)
        glTexCoord2f(1, 0); glVertex3f(max_x, 0, min_z)
        glTexCoord2f(1, 1); glVertex3f(max_x, h, min_z)
        glTexCoord2f(0, 1); glVertex3f(min_x, h, min_z)
        glEnd()

        # Back face (facing +Z)
        glBegin(GL_QUADS)
        glNormal3f(0, 0, 1)
        glTexCoord2f(0, 0); glVertex3f(max_x, 0, max_z)
        glTexCoord2f(1, 0); glVertex3f(min_x, 0, max_z)
        glTexCoord2f(1, 1); glVertex3f(min_x, h, max_z)
        glTexCoord2f(0, 1); glVertex3f(max_x, h, max_z)
        glEnd()

        # Left face (facing -X)
        glBegin(GL_QUADS)
        glNormal3f(-1, 0, 0)
        glTexCoord2f(0, 0); glVertex3f(min_x, 0, max_z)
        glTexCoord2f(1, 0); glVertex3f(min_x, 0, min_z)
        glTexCoord2f(1, 1); glVertex3f(min_x, h, min_z)
        glTexCoord2f(0, 1); glVertex3f(min_x, h, max_z)
        glEnd()

        # Right face (facing +X)
        glBegin(GL_QUADS)
        glNormal3f(1, 0, 0)
        glTexCoord2f(0, 0); glVertex3f(max_x, 0, min_z)
        glTexCoord2f(1, 0); glVertex3f(max_x, 0, max_z)
        glTexCoord2f(1, 1); glVertex3f(max_x, h, max_z)
        glTexCoord2f(0, 1); glVertex3f(max_x, h, min_z)
        glEnd()

        # Top face
        glBegin(GL_QUADS)
        glNormal3f(0, 1, 0)
        glTexCoord2f(0, 0); glVertex3f(min_x, h, min_z)
        glTexCoord2f(1, 0); glVertex3f(max_x, h, min_z)
        glTexCoord2f(1, 1); glVertex3f(max_x, h, max_z)
        glTexCoord2f(0, 1); glVertex3f(min_x, h, max_z)
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
