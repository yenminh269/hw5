#!/usr/bin/env python3
"""
COSC 4370 Homework #5
Interactive 3D Maze Game with FPS Controls
"""

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import random
import time
import math
from maze_generator import MazeGenerator
from fps_camera import FPSCamera
from maze_renderer import MazeRenderer
from special_tiles import SpecialTileManager

class MazeGame:
    def __init__(self, maze_size=15):
        pygame.init()
        self.display = (1200, 800)
        self.screen = pygame.display.set_mode(self.display, DOUBLEBUF | OPENGL)
        pygame.display.set_caption("3D Maze Explorer - COSC 4370 HW5")

        # Hide and capture mouse
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

        # Mouse control setup
        self.display_center = [self.display[i] // 2 for i in range(2)]
        pygame.mouse.set_pos(self.display_center)

        self.maze_size = maze_size

        # FPS tracking
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 18)

        # Setup OpenGL
        self.setup_opengl()

        # Initialize game components
        self.maze_generator = MazeGenerator(maze_size)
        self.maze = None
        self.camera = None
        self.renderer = None
        self.special_tiles = None

        # Game state
        self.start_time = None
        self.elapsed_time = 0
        self.running = True
        self.paused = False
        self.game_won = False
        self.win_time = 0

        # On-screen notification system
        self.notifications = []  # List of {text, color, expire_time, size}
        self.large_font = pygame.font.SysFont("Arial", 32, bold=True)
        self.title_font = pygame.font.SysFont("Arial", 64, bold=True)

        # Mouse sensitivity (adjustable with +/-)
        self.mouse_sensitivity = 0.2

        # Generate initial maze
        self.generate_new_maze()

        # Show welcome message
        self.show_notification("Navigate to the GREEN goal! Press H for hints", (200, 255, 200), 4.0, large=True)

    def setup_opengl(self):
        """Configure OpenGL settings"""
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        # Setup lights
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1])
        glLightfv(GL_LIGHT0, GL_POSITION, [0, 0, 10, 1])

        # Add a second light for better visibility
        glEnable(GL_LIGHT1)
        glLightfv(GL_LIGHT1, GL_AMBIENT, [0.2, 0.2, 0.2, 1])
        glLightfv(GL_LIGHT1, GL_DIFFUSE, [0.5, 0.5, 0.5, 1])

        # Projection
        glMatrixMode(GL_PROJECTION)
        gluPerspective(70, (self.display[0] / self.display[1]), 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

        # Disable fog for clearer visuals (was causing blur)
        glDisable(GL_FOG)

    def generate_new_maze(self):
        """Generate a new random maze"""
        self.maze = self.maze_generator.generate()

        # Find start position (entrance) - typically at (0, 0)
        start_x, start_y = 0.5, 0.5

        # Initialize camera at start position
        self.camera = FPSCamera(start_x, start_y, 0.5, self.maze_size)

        # Initialize renderer with new maze
        self.renderer = MazeRenderer(self.maze, self.maze_size)

        # Initialize special tiles
        self.special_tiles = SpecialTileManager(self.maze, self.maze_size)

        # Reset timer and win state
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
        """Add an on-screen notification message (only 1 at a time)"""
        # Clear existing notifications - only show 1 at a time
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
                    # Reset to start
                    self.reset_position()
                    self.show_notification("Position Reset!", (255, 200, 100), 2.0, large=True)
                elif event.key == pygame.K_n:
                    # Generate new maze
                    self.generate_new_maze()
                    self.show_notification("New Maze Generated!", (100, 255, 200), 2.0, large=True)
                elif event.key == pygame.K_h:
                    # Use hint (if available)
                    if self.special_tiles.hints_remaining > 0:
                        self.special_tiles.use_hint()
                        self.show_notification(f"Hint Activated! ({self.special_tiles.hints_remaining} left)", (255, 150, 50), 2.0)
                    else:
                        self.show_notification("No hints remaining!", (255, 100, 100), 1.5)
                elif event.key == pygame.K_p:
                    # Pause/unpause
                    self.paused = not self.paused
                    # Recenter mouse when unpausing
                    if not self.paused:
                        pygame.mouse.set_pos(self.display_center)
                elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                    # Increase mouse sensitivity
                    self.mouse_sensitivity = min(0.5, self.mouse_sensitivity + 0.05)
                    self.camera.mouse_sensitivity = self.mouse_sensitivity
                    self.show_notification(f"Sensitivity: {self.mouse_sensitivity:.2f}", (200, 200, 255), 1.0)
                elif event.key == pygame.K_MINUS:
                    # Decrease mouse sensitivity
                    self.mouse_sensitivity = max(0.05, self.mouse_sensitivity - 0.05)
                    self.camera.mouse_sensitivity = self.mouse_sensitivity
                    self.show_notification(f"Sensitivity: {self.mouse_sensitivity:.2f}", (200, 200, 255), 1.0)

            if event.type == pygame.MOUSEMOTION and not self.paused:
                # Handle mouse movement for camera rotation
                mouse_move = [event.pos[i] - self.display_center[i] for i in range(2)]
                if mouse_move[0] != 0 or mouse_move[1] != 0:
                    self.camera.rotate(mouse_move[0], mouse_move[1])

        # Continuously recenter mouse during gameplay
        if not self.paused:
            pygame.mouse.set_pos(self.display_center)

    def update(self, dt):
        """Update game state"""
        if self.paused:
            return

        # Update elapsed time
        self.elapsed_time = time.time() - self.start_time

        # Update camera launch physics
        self.camera.update_launch(dt)

        # Get keyboard state for movement
        keys = pygame.key.get_pressed()

        # Calculate movement
        move_x, move_z = 0, 0
        if keys[K_w]:
            move_z = 1  # Forward
        if keys[K_s]:
            move_z = -1  # Backward
        if keys[K_a]:
            move_x = -1  # Strafe left
        if keys[K_d]:
            move_x = 1  # Strafe right

        # Update camera with collision detection
        if move_x != 0 or move_z != 0:
            self.camera.move(move_x, move_z, dt, self.maze)

        # Check for special tile effects
        cell_x = int(self.camera.x)
        cell_y = int(self.camera.z)

        if 0 <= cell_x < self.maze_size and 0 <= cell_y < self.maze_size:
            effect = self.special_tiles.check_tile(cell_x, cell_y)
            if effect:
                self.apply_effect(effect)

        # Update special tiles (for animations, cooldowns, etc.)
        self.special_tiles.update(dt)

        # Update camera with current speed modifier
        self.camera.speed_modifier = self.special_tiles.speed_modifier

        # Update light position to follow player
        glLightfv(GL_LIGHT1, GL_POSITION, [self.camera.x, 2, self.camera.z, 1])

        # Check win condition
        if self.check_win_condition():
            self.handle_win()

    def apply_effect(self, effect):
        """Apply special tile effect to player"""
        if effect['type'] == 'trap_reset':
            self.reset_position()
            self.show_notification("TRAP! Back to Start!", (255, 50, 50), 2.5, large=True)
        elif effect['type'] == 'trap_turn':
            self.camera.yaw += 90
            self.show_notification("DIZZY! Turned 90°", (200, 50, 200), 2.0, large=True)
        elif effect['type'] == 'powerup_launch':
            self.camera.launch()
            self.show_notification("LAUNCHED! Look around!", (255, 255, 50), 3.0, large=True)
        elif effect['type'] == 'speed_slow':
            self.show_notification("Slow Zone...", (100, 150, 255), 1.5)
        elif effect['type'] == 'speed_fast':
            self.show_notification("SPEED BOOST!", (50, 255, 50), 1.5)

    def check_win_condition(self):
        """Check if player reached the goal"""
        cell_x = int(self.camera.x)
        cell_y = int(self.camera.z)

        # Goal is at bottom-right corner
        return cell_x == self.maze_size - 1 and cell_y == self.maze_size - 1

    def handle_win(self):
        """Handle winning the maze"""
        self.game_won = True
        self.win_time = self.elapsed_time
        self.paused = True

    def render_win_screen(self):
        """Render the victory screen overlay"""
        # Switch to 2D rendering
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.display[0], self.display[1], 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)

        # Semi-transparent dark overlay
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0, 0, 0, 0.7)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(self.display[0], 0)
        glVertex2f(self.display[0], self.display[1])
        glVertex2f(0, self.display[1])
        glEnd()

        # Draw decorative border
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

        # Center coordinates
        center_x = self.display[0] // 2
        center_y = self.display[1] // 2

        # Draw "MAZE COMPLETE!" title
        title_text = "MAZE COMPLETE!"
        title_surface = self.title_font.render(title_text, True, (50, 255, 50))
        title_x = center_x - title_surface.get_width() // 2
        title_y = center_y - 100

        # Draw title with glow effect
        glow_surface = self.title_font.render(title_text, True, (100, 255, 100))
        self.draw_text_at(glow_surface, title_x - 2, title_y - 2)
        self.draw_text_at(title_surface, title_x, title_y)

        # Draw time
        time_text = f"Time: {self.win_time:.2f} seconds"
        time_surface = self.large_font.render(time_text, True, (255, 255, 100))
        time_x = center_x - time_surface.get_width() // 2
        self.draw_text_at(time_surface, time_x, center_y - 20)

        # Draw instructions
        instructions = [
            ("Press N for New Maze", (100, 200, 255)),
            ("Press R to Retry", (255, 200, 100)),
            ("Press ESC to Quit", (200, 200, 200))
        ]
        for i, (text, color) in enumerate(instructions):
            inst_surface = self.font.render(text, True, color)
            inst_x = center_x - inst_surface.get_width() // 2
            self.draw_text_at(inst_surface, inst_x, center_y + 40 + i * 35)

        # Restore 3D rendering
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

        # Apply camera transformation
        self.camera.apply()

        # Render maze
        self.renderer.render()

        # Render special tiles with effects
        self.special_tiles.render(self.camera)

        # Render goal marker
        self.render_goal()

        # Render HUD (timer, position, hints)
        self.render_hud()

        # Render win screen overlay if game won
        if self.game_won:
            self.render_win_screen()

        pygame.display.flip()

    def render_goal(self):
        """Draw a special marker at the goal location"""
        x, z = self.maze_size - 1, self.maze_size - 1

        glDisable(GL_LIGHTING)

        # Pulsing green light at goal
        pulse = 0.5 + 0.5 * abs((time.time() * 2) % 2 - 1)

        # Draw glowing floor marker
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glColor4f(0, pulse, 0, 0.7)
        glBegin(GL_QUADS)
        glVertex3f(x + 0.1, 0.02, z + 0.1)
        glVertex3f(x + 0.9, 0.02, z + 0.1)
        glVertex3f(x + 0.9, 0.02, z + 0.9)
        glVertex3f(x + 0.1, 0.02, z + 0.9)
        glEnd()

        # Draw vertical beam
        glColor4f(0, pulse, 0, 0.3)
        glBegin(GL_LINES)
        glVertex3f(x + 0.5, 0, z + 0.5)
        glVertex3f(x + 0.5, 2.0, z + 0.5)
        glEnd()

        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)

    def render_hud(self):
        """Render heads-up display with game info"""
        # Switch to 2D rendering
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.display[0], self.display[1], 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)

        # Render semi-transparent background for HUD
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Top-left info panel
        glColor4f(0, 0, 0, 0.5)
        glBegin(GL_QUADS)
        glVertex2f(10, 10)
        glVertex2f(250, 10)
        glVertex2f(250, 150)
        glVertex2f(10, 150)
        glEnd()

        # Draw crosshair in center
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

        # Calculate distance to goal
        goal_x, goal_z = self.maze_size - 0.5, self.maze_size - 0.5
        distance = math.sqrt((self.camera.x - goal_x)**2 + (self.camera.z - goal_z)**2)

        # Draw text using optimized method
        fps = self.clock.get_fps()
        self.draw_text_optimized(f"FPS: {fps:.1f}", 20, 20, (100, 255, 100))
        self.draw_text_optimized(f"Time: {self.elapsed_time:.1f}s", 20, 45, (255, 255, 255))
        self.draw_text_optimized(f"Position: ({int(self.camera.x)}, {int(self.camera.z)})", 20, 70, (255, 200, 100))
        self.draw_text_optimized(f"Distance: {distance:.1f}", 20, 95, (100, 255, 100) if distance < 5 else (255, 255, 255))
        self.draw_text_optimized(f"Hints: {self.special_tiles.hints_remaining}", 20, 120, (255, 255, 255))

        # Speed indicator
        if self.special_tiles.speed_modifier != 1.0:
            speed_text = "FAST!" if self.special_tiles.speed_modifier > 1.0 else "SLOW"
            color = (0, 255, 0) if self.special_tiles.speed_modifier > 1.0 else (255, 128, 0)
            self.draw_text_optimized(speed_text, 20, 120, color)

        # Launch indicator and minimap when airborne
        if self.camera.is_launched:
            self.draw_text_optimized("AIRBORNE!", 20, 145, (255, 255, 0))
            self.render_minimap()

        # Render center notifications
        self.render_notifications()

        # Instructions at bottom
        if self.paused:
            self.draw_text_optimized("PAUSED - Press P to continue", self.display[0]//2 - 150, self.display[1] - 50, color=(255, 255, 0))

        # Controls reminder (small, bottom-right)
        controls = [
            "WASD: Move | Mouse: Look | +/-: Sensitivity",
            "R: Reset | N: New Maze | H: Hint | P: Pause"
        ]
        for i, ctrl in enumerate(controls):
            self.draw_text_optimized(ctrl, self.display[0] - 420, self.display[1] - 60 + i*25, (180, 180, 180))

        # Restore 3D rendering
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

    def render_notifications(self):
        """Render center-screen notification messages"""
        current_time = time.time()

        # Remove expired notifications
        self.notifications = [n for n in self.notifications if n['expire_time'] > current_time]

        # Render active notifications in center of screen
        center_x = self.display[0] // 2
        start_y = self.display[1] // 3

        for i, notif in enumerate(self.notifications):
            # Calculate fade based on remaining time
            remaining = notif['expire_time'] - current_time
            alpha = min(1.0, remaining / 0.5)  # Fade out in last 0.5 seconds

            # Choose font based on size
            font = self.large_font if notif.get('large') else self.font

            # Render with alpha
            color = notif['color']
            faded_color = (
                int(color[0] * alpha),
                int(color[1] * alpha),
                int(color[2] * alpha)
            )

            # Create text surface
            text_surface = font.render(notif['text'], True, faded_color)
            text_width = text_surface.get_width()

            # Center horizontally
            x = center_x - text_width // 2
            y = start_y + i * 45

            # Draw background box for better visibility
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

            # Draw the text
            text_data = pygame.image.tostring(text_surface, "RGBA", True)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glWindowPos2d(x, self.display[1] - y - text_surface.get_height())
            glDrawPixels(text_surface.get_width(), text_surface.get_height(),
                        GL_RGBA, GL_UNSIGNED_BYTE, text_data)
            glDisable(GL_BLEND)

    def draw_text_optimized(self, text, x, y, color=(255, 255, 255)):
        """Draw 2D text on screen using optimized method"""
        text_surface = self.font.render(text, True, color, (0, 0, 0))
        text_data = pygame.image.tostring(text_surface, "RGBA", True)

        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Use glWindowPos2d for more efficient positioning
        glWindowPos2d(x, self.display[1] - y - text_surface.get_height())
        glDrawPixels(text_surface.get_width(), text_surface.get_height(),
                     GL_RGBA, GL_UNSIGNED_BYTE, text_data)

        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)

    def render_minimap(self):
        """Render a minimap in the corner when airborne"""
        # Minimap settings
        map_size = 200
        map_x = self.display[0] - map_size - 20
        map_y = 20
        cell_size = map_size / self.maze_size

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Draw background
        glColor4f(0, 0, 0, 0.7)
        glBegin(GL_QUADS)
        glVertex2f(map_x - 5, map_y - 5)
        glVertex2f(map_x + map_size + 5, map_y - 5)
        glVertex2f(map_x + map_size + 5, map_y + map_size + 5)
        glVertex2f(map_x - 5, map_y + map_size + 5)
        glEnd()

        # Draw maze walls
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

        # Draw special tiles
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

            # Draw small dot
            glPointSize(4)
            glBegin(GL_POINTS)
            glVertex2f(cx, cy)
            glEnd()

        # Draw goal (green)
        goal_x = map_x + (self.maze_size - 0.5) * cell_size
        goal_y = map_y + (self.maze_size - 0.5) * cell_size
        glColor4f(0, 1, 0, 1.0)
        glPointSize(8)
        glBegin(GL_POINTS)
        glVertex2f(goal_x, goal_y)
        glEnd()

        # Draw player position (white with pulse)
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
        print("3D MAZE EXPLORER - COSC 4370 HW5")
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
            dt = self.clock.tick(60) / 1000.0  # Delta time in seconds

            self.handle_events()
            self.update(dt)
            self.render()

        pygame.quit()

def main():
    game = MazeGame(maze_size=15)
    game.run()

if __name__ == '__main__':
    main()
