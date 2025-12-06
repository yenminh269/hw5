"""
Maze Generator using Recursive Backtracking Algorithm
Creates perfect mazes with exactly one solution path
"""

import random

class MazeGenerator:
    def __init__(self, size):
        self.size = size
        self.maze = None

    def generate(self):
        """Generate a new random maze using recursive backtracking"""
        # Initialize maze grid
        # Each cell stores which walls exist: [North, East, South, West]
        self.maze = [[{'N': True, 'E': True, 'S': True, 'W': True, 'visited': False}
                      for _ in range(self.size)] for _ in range(self.size)]

        # Start from top-left corner
        self._carve_path(0, 0)

        # Mark all cells as unvisited for pathfinding later
        for row in self.maze:
            for cell in row:
                cell['visited'] = False

        # Remove entrance and exit walls
        self.maze[0][0]['N'] = False  # Entrance at top-left
        self.maze[self.size-1][self.size-1]['S'] = False  # Exit at bottom-right

        return self.maze

    def _carve_path(self, x, y):
        """Recursively carve paths through the maze"""
        self.maze[y][x]['visited'] = True

        # Define directions: (dx, dy, direction, opposite)
        directions = [
            (0, -1, 'N', 'S'),  # North
            (1, 0, 'E', 'W'),   # East
            (0, 1, 'S', 'N'),   # South
            (-1, 0, 'W', 'E')   # West
        ]

        # Randomize direction order
        random.shuffle(directions)

        for dx, dy, direction, opposite in directions:
            nx, ny = x + dx, y + dy

            # Check if neighbor is valid and unvisited
            if (0 <= nx < self.size and 0 <= ny < self.size and
                not self.maze[ny][nx]['visited']):

                # Remove walls between current cell and neighbor
                self.maze[y][x][direction] = False
                self.maze[ny][nx][opposite] = False

                # Recursively visit neighbor
                self._carve_path(nx, ny)

    def has_wall(self, x, y, direction):
        """Check if a wall exists at given position and direction"""
        if not (0 <= x < self.size and 0 <= y < self.size):
            return True
        return self.maze[y][x].get(direction, True)

    def get_solution_path(self):
        """
        Find the solution path from start to end using BFS
        Returns list of (x, y) coordinates
        """
        from collections import deque

        start = (0, 0)
        end = (self.size - 1, self.size - 1)

        # Reset visited flags
        for row in self.maze:
            for cell in row:
                cell['visited'] = False

        queue = deque([start])
        parent = {start: None}
        self.maze[0][0]['visited'] = True

        # BFS to find shortest path
        while queue:
            x, y = queue.popleft()

            if (x, y) == end:
                # Reconstruct path
                path = []
                current = end
                while current is not None:
                    path.append(current)
                    current = parent[current]
                return list(reversed(path))

            # Check all four directions
            directions = [
                (0, -1, 'N'),  # North
                (1, 0, 'E'),   # East
                (0, 1, 'S'),   # South
                (-1, 0, 'W')   # West
            ]

            for dx, dy, direction in directions:
                nx, ny = x + dx, y + dy

                if (0 <= nx < self.size and 0 <= ny < self.size and
                    not self.maze[ny][nx]['visited'] and
                    not self.maze[y][x][direction]):

                    self.maze[ny][nx]['visited'] = True
                    parent[(nx, ny)] = (x, y)
                    queue.append((nx, ny))

        # Reset visited flags
        for row in self.maze:
            for cell in row:
                cell['visited'] = False

        return []

    def print_maze(self):
        """Print ASCII representation of maze (for debugging)"""
        for y in range(self.size):
            # Print top walls
            line = ""
            for x in range(self.size):
                line += "+"
                line += "---" if self.maze[y][x]['N'] else "   "
            line += "+"
            print(line)

            # Print side walls
            line = ""
            for x in range(self.size):
                line += "|" if self.maze[y][x]['W'] else " "
                line += "   "
            line += "|" if self.maze[y][self.size-1]['E'] else " "
            print(line)

        # Print bottom wall
        line = ""
        for x in range(self.size):
            line += "+"
            line += "---" if self.maze[self.size-1][x]['S'] else "   "
        line += "+"
        print(line)
