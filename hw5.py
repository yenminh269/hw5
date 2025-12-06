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

        # Generate initial maze
        self.generate_new_maze()

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

        # Enable fog for atmosphere
        glEnable(GL_FOG)
        glFogi(GL_FOG_MODE, GL_LINEAR)
        glFogfv(GL_FOG_COLOR, [0.1, 0.1, 0.15, 1])
        glFogf(GL_FOG_DENSITY, 0.35)
        glFogf(GL_FOG_START, 10.0)
        glFogf(GL_FOG_END, 40.0)

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

        # Reset timer
        self.start_time = time.time()
        self.elapsed_time = 0

    def reset_position(self):
        """Reset player to start position without regenerating maze"""
        self.camera.reset_position(0.5, 0.5)
        self.start_time = time.time()
        self.elapsed_time = 0
        self.special_tiles.reset_effects()

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
                    print("Position reset!")
                elif event.key == pygame.K_n:
                    # Generate new maze
                    self.generate_new_maze()
                    print("New maze generated!")
                elif event.key == pygame.K_h:
                    # Use hint (if available)
                    self.special_tiles.use_hint()
                elif event.key == pygame.K_p:
                    # Pause/unpause
                    self.paused = not self.paused
                    # Recenter mouse when unpausing
                    if not self.paused:
                        pygame.mouse.set_pos(self.display_center)

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
            print("TRAP! Reset to start!")
        elif effect['type'] == 'trap_turn':
            self.camera.yaw += 90
            print("Dizzy! Turned 90 degrees!")
        elif effect['type'] == 'powerup_launch':
            self.camera.launch()
            print("LAUNCH! Bird's eye view!")
        elif effect['type'] == 'speed_slow':
            print("Slow zone...")
        elif effect['type'] == 'speed_fast':
            print("Speed boost!")

    def check_win_condition(self):
        """Check if player reached the goal"""
        cell_x = int(self.camera.x)
        cell_y = int(self.camera.z)

        # Goal is at bottom-right corner
        return cell_x == self.maze_size - 1 and cell_y == self.maze_size - 1

    def handle_win(self):
        """Handle winning the maze"""
        print(f"\n{'='*50}")
        print(f"CONGRATULATIONS! You completed the maze!")
        print(f"Time: {self.elapsed_time:.2f} seconds")
        print(f"{'='*50}\n")
        print("Press N for new maze, R to retry, or ESC to quit")
        self.paused = True

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
        glVertex2f(250, 125)
        glVertex2f(10, 125)
        glEnd()

        glDisable(GL_BLEND)

        # Draw text using optimized method
        fps = self.clock.get_fps()
        self.draw_text_optimized(f"FPS: {fps:.1f}", 20, 20, (100, 255, 100))
        self.draw_text_optimized(f"Time: {self.elapsed_time:.1f}s", 20, 45, (255, 255, 255))
        self.draw_text_optimized(f"Position: ({int(self.camera.x)}, {int(self.camera.z)})", 20, 70, (255, 200, 100))
        self.draw_text_optimized(f"Hints: {self.special_tiles.hints_remaining}", 20, 95, (255, 255, 255))

        # Speed indicator
        if self.special_tiles.speed_modifier != 1.0:
            speed_text = "FAST!" if self.special_tiles.speed_modifier > 1.0 else "SLOW"
            color = (0, 255, 0) if self.special_tiles.speed_modifier > 1.0 else (255, 128, 0)
            self.draw_text_optimized(speed_text, 20, 120, color)

        # Launch indicator
        if self.camera.is_launched:
            self.draw_text_optimized("AIRBORNE!", 20, 145, (255, 255, 0))

        # Instructions at bottom
        if self.paused:
            self.draw_text_optimized("PAUSED - Press P to continue", self.display[0]//2 - 150, self.display[1] - 50, color=(255, 255, 0))

        # Controls reminder (small, bottom-right)
        controls = [
            "WASD: Move | Mouse: Look",
            "R: Reset | N: New Maze | H: Hint"
        ]
        for i, ctrl in enumerate(controls):
            self.draw_text_optimized(ctrl, self.display[0] - 350, self.display[1] - 60 + i*25, (180, 180, 180))

        # Restore 3D rendering
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

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
