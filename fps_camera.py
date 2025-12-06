"""
First-Person Camera Controller with Mouse Look and Collision Detection
"""

import math
from OpenGL.GL import *
from OpenGL.GLU import *

class FPSCamera:
    def __init__(self, x, z, y, maze_size):
        # Position
        self.x = x
        self.y = y  # Height above ground
        self.z = z
        self.maze_size = maze_size

        # Initial position for reset
        self.initial_x = x
        self.initial_z = z

        # Rotation
        self.yaw = -90    # Horizontal rotation (left/right) - start facing +X direction
        self.pitch = 0  # Vertical rotation (up/down)

        # Movement
        self.base_speed = 3.0
        self.speed_modifier = 1.0
        self.mouse_sensitivity = 0.2

        # Collision
        self.radius = 0.2  # Player collision radius

        # Launch effect
        self.is_launched = False
        self.launch_height = 0
        self.launch_velocity = 0

        # Ground height
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

        # Clamp pitch to prevent flipping
        self.pitch = max(-89, min(89, self.pitch))

    def move(self, move_x, move_z, dt, maze):
        """
        Move camera with collision detection
        move_x: -1 (left), 0 (none), 1 (right)
        move_z: -1 (back), 0 (none), 1 (forward)
        """
        if self.is_launched:
            # Update launch physics
            self.update_launch(dt)
            return

        # Calculate movement direction based on camera orientation
        yaw_rad = math.radians(self.yaw)

        # Forward/backward movement
        forward_x = -math.sin(yaw_rad) * move_z
        forward_z = -math.cos(yaw_rad) * move_z

        # Strafe left/right movement
        strafe_x = math.sin(yaw_rad + math.pi/2) * move_x
        strafe_z = math.cos(yaw_rad + math.pi/2) * move_x

        # Combined movement
        dx = (forward_x + strafe_x) * self.base_speed * self.speed_modifier * dt
        dz = (forward_z + strafe_z) * self.base_speed * self.speed_modifier * dt

        # Try to move and check collisions
        new_x = self.x + dx
        new_z = self.z + dz

        # Check collision for X movement
        if not self.check_collision(new_x, self.z, maze):
            self.x = new_x

        # Check collision for Z movement
        if not self.check_collision(self.x, new_z, maze):
            self.z = new_z

    def check_collision(self, x, z, maze):
        """
        Check if position collides with walls
        Returns True if collision detected
        """
        # Check bounds
        if x < 0 or x >= self.maze_size or z < 0 or z >= self.maze_size:
            return True

        # Get current cell
        cell_x = int(x)
        cell_y = int(z)

        if not (0 <= cell_x < self.maze_size and 0 <= cell_y < self.maze_size):
            return True

        # Check collision with walls in current cell
        cell = maze[cell_y][cell_x]

        # Position within cell (0.0 to 1.0)
        local_x = x - cell_x
        local_z = z - cell_y

        # Check North wall (z close to 0)
        if cell['N'] and local_z < self.radius:
            return True

        # Check South wall (z close to 1)
        if cell['S'] and local_z > 1 - self.radius:
            return True

        # Check West wall (x close to 0)
        if cell['W'] and local_x < self.radius:
            return True

        # Check East wall (x close to 1)
        if cell['E'] and local_x > 1 - self.radius:
            return True

        return False

    def launch(self):
        """Launch player into the air for bird's eye view"""
        if not self.is_launched:
            self.is_launched = True
            self.launch_velocity = 8.0  # Initial upward velocity

    def update_launch(self, dt):
        """Update launch physics"""
        gravity = 15.0

        # Update velocity and height
        self.launch_velocity -= gravity * dt
        self.launch_height += self.launch_velocity * dt

        # Update camera height
        self.y = self.ground_height + self.launch_height

        # Land when reaching ground
        if self.launch_height <= 0:
            self.launch_height = 0
            self.y = self.ground_height
            self.is_launched = False
            self.launch_velocity = 0

    def apply(self):
        """Apply camera transformation to OpenGL"""
        glLoadIdentity()

        # Apply pitch (up/down) and yaw (left/right) rotation
        glRotatef(self.pitch, 1, 0, 0)
        glRotatef(-self.yaw, 0, 1, 0)  # Negate yaw for correct OpenGL rotation

        # Move camera to position (negative because we move the world)
        glTranslatef(-self.x, -self.y, -self.z)

    def get_forward_vector(self):
        """Get the forward direction vector"""
        yaw_rad = math.radians(self.yaw)
        return (math.sin(yaw_rad), 0, math.cos(yaw_rad))

    def get_right_vector(self):
        """Get the right direction vector"""
        yaw_rad = math.radians(self.yaw)
        return (math.sin(yaw_rad + math.pi/2), 0, math.cos(yaw_rad + math.pi/2))
