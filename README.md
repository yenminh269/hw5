# COSC 4370 Homework #5 - 3D Maze Explorer

An interactive 3D maze game featuring FPS controls, special tiles, and dynamic gameplay.

## Features Implemented

### 1. Core Requirements 
- **Maze Generation**: Random 10x10+ maze (default 15x15) using recursive backtracking algorithm
- **FPS Controls**:
  - WASD for movement
  - Mouse for camera rotation
  - Smooth first-person perspective
- **Reset Mechanism**: Press 'R' to start over at the entrance to the maze (time and position reset)
- **Regenerate Maze**: Press 'N' to restart and re-randomize the maze (time and position reset)
- **Pause System**: Press 'P' to pause/unpause
- **Collision Detection**: Cannot clip through walls or floor
- **Timer Display**: Tracks and displays elapsed time in top-left corner
- **Position Display**: Shows current cell position (x, z)

### 2. Special Tiles & Effects 

#### Traps (Hinder Player)
1. **Red Tiles** (Dead Ends): Reset player to start position
2. **Purple Tiles** (Dead Ends): Turn player 90 degrees when entered
3. **Blue Tiles** (Off Main Path): Slow zones (0.4x speed)

#### Power-ups (Assist Player)
1. **Green Tiles** (Main Path): Speed up the player along the main path (1.8x speed)
2. **Yellow Tiles** (Launch Pads): Launch player above the wall to have a look at the maze
3. **Orange Hint System**: Press 'H' to reveal solution path (limited to 3 hints, 5 seconds each)

### 3. Visual Features 
- **Textured Walls**: Procedural brick texture
- **Textured Floor**: Checkered pattern
- **Textured Ceiling**: Dark atmospheric ceiling
- **Animated Special Tiles**: Pulsing colored overlays on floor
- **Goal Marker**: Pulsing green beacon at exit
- **Lighting**: Two-light setup with fog for atmosphere
- **HUD Elements**: FPS, time, position, hints, status indicators

### 4. Additional Features
- **Launch Physics**: Gravity simulation for launch pads
- **Solution Path**: BFS algorithm finds optimal path
- **Smart Tile Placement**: Special tiles placed strategically
- **Visual Feedback**: Status indicators for speed changes and launch state

## File Structure

```
hw5/
├── hw5_submit.py    # Main game file (run this)
└── README.md        # This file
```

## How to Run

```bash
python hw5_submit.py
```

## Controls

| Key | Action |
|-----|--------|
| W/A/S/D | Move forward/left/backward/right |
| Mouse | Look around (rotate camera) |
| R | Reset to entrance (keeps same maze) |
| N | Generate new random maze |
| H | Use hint (shows path for 5 seconds) |
| P | Pause/Unpause |
| ESC | Quit game |

## Gameplay

1. **Objective**: Navigate from entrance (top-left) to exit (bottom-right)
2. **Strategy**:
   - Green tiles speed you up - these are on the main path
   - Blue tiles slow you down - avoid these
   - Yellow tiles launch you - use for aerial reconnaissance
   - Red/Purple tiles are traps - avoid dead ends
   - Use hints sparingly (only 3 available)

## Technical Details

### Collision System
- Circular collision detection with wall segments
- Smooth sliding along walls
- Cannot clip through any walls

### Camera System
- Smooth mouse look with pitch limiting (-89° to +89°)
- Velocity-based movement with delta time
- Launch physics with gravity simulation

### Maze Algorithm
- Recursive backtracking 
- BFS pathfinding for solution
- Dead-end detection for trap placement


## Dependencies

- Python 3.x
- pygame
- PyOpenGL
- PyOpenGL-accelerate (recommended)

Install with:
```bash
pip install pygame PyOpenGL PyOpenGL-accelerate
```
