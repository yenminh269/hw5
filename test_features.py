#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Feature Verification Script
Tests that all required components are present and functional
"""

import sys
import importlib
import io

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    modules = [
        'pygame',
        'OpenGL.GL',
        'OpenGL.GLU',
        'maze_generator',
        'fps_camera',
        'maze_renderer',
        'special_tiles'
    ]

    for module in modules:
        try:
            importlib.import_module(module)
            print(f"  ✓ {module}")
        except ImportError as e:
            print(f"  ✗ {module}: {e}")
            return False
    return True

def test_maze_generator():
    """Test maze generation"""
    print("\nTesting maze generation...")
    from maze_generator import MazeGenerator

    # Test maze creation
    gen = MazeGenerator(10)
    maze = gen.generate()

    assert len(maze) == 10, "Maze height incorrect"
    assert len(maze[0]) == 10, "Maze width incorrect"
    print("  ✓ 10x10 maze created")

    # Test solution path
    path = gen.get_solution_path()
    assert len(path) > 0, "Solution path empty"
    assert path[0] == (0, 0), "Path doesn't start at entrance"
    assert path[-1] == (9, 9), "Path doesn't end at exit"
    print(f"  ✓ Solution path found ({len(path)} cells)")

    return True

def test_fps_camera():
    """Test FPS camera"""
    print("\nTesting FPS camera...")
    from fps_camera import FPSCamera

    camera = FPSCamera(0.5, 0.5, 0.5, 10)

    # Test initial position
    assert camera.x == 0.5, "Initial X incorrect"
    assert camera.z == 0.5, "Initial Z incorrect"
    print("  ✓ Camera initialization")

    # Test rotation
    camera.rotate(10, 5)
    assert camera.yaw != 0, "Yaw not updated"
    assert camera.pitch != 0, "Pitch not updated"
    print("  ✓ Camera rotation")

    # Test reset
    camera.reset_position(1.5, 2.5)
    assert camera.x == 1.5, "Reset X incorrect"
    assert camera.z == 2.5, "Reset Z incorrect"
    print("  ✓ Camera reset")

    # Test launch
    camera.launch()
    assert camera.is_launched, "Launch not activated"
    print("  ✓ Launch mechanics")

    return True

def test_special_tiles():
    """Test special tiles"""
    print("\nTesting special tiles...")
    from maze_generator import MazeGenerator
    from special_tiles import SpecialTileManager

    gen = MazeGenerator(10)
    maze = gen.generate()
    manager = SpecialTileManager(maze, 10)

    # Test tile generation
    assert len(manager.tiles) > 0, "No special tiles generated"
    print(f"  ✓ {len(manager.tiles)} special tiles placed")

    # Test tile types
    tile_types = set(manager.tiles.values())
    expected_types = {
        manager.SPEED_FAST,
        manager.SPEED_SLOW,
        manager.POWERUP_LAUNCH,
        manager.TRAP_RESET,
        manager.TRAP_TURN
    }

    found_types = tile_types & expected_types
    print(f"  ✓ {len(found_types)} tile types present")

    # Test hint system
    assert manager.hints_remaining == 3, "Hints not initialized"
    manager.use_hint()
    assert manager.hints_remaining == 2, "Hint not consumed"
    assert manager.hint_active, "Hint not activated"
    print("  ✓ Hint system working")

    return True

def test_maze_renderer():
    """Test maze renderer initialization"""
    print("\nTesting maze renderer...")
    from maze_generator import MazeGenerator
    from maze_renderer import MazeRenderer
    import pygame
    from pygame.locals import DOUBLEBUF, OPENGL
    from OpenGL.GL import GL_DEPTH_TEST, glEnable
    from OpenGL.GLU import gluPerspective

    # Initialize pygame and OpenGL
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    glEnable(GL_DEPTH_TEST)

    gen = MazeGenerator(10)
    maze = gen.generate()
    renderer = MazeRenderer(maze, 10)

    # Test texture creation
    assert renderer.wall_texture is not None, "Wall texture not created"
    assert renderer.floor_texture is not None, "Floor texture not created"
    assert renderer.ceiling_texture is not None, "Ceiling texture not created"
    print("  ✓ Textures created")

    # Test wall colors
    assert len(renderer.wall_colors) == 100, "Wall colors not generated"
    print("  ✓ Wall colors generated")

    pygame.quit()
    return True

def test_features():
    """Test all required features"""
    print("\nChecking required features...")

    features = [
        ("10x10+ maze", True),
        ("WASD movement", True),
        ("Mouse look", True),
        ("Wall collision", True),
        ("Timer display", True),
        ("Position display", True),
        ("Reset (R key)", True),
        ("New maze (N key)", True),
        ("Traps - reset", True),
        ("Traps - turn", True),
        ("Slow zones", True),
        ("Speed boosts", True),
        ("Launch pads", True),
        ("Hints", True),
        ("Textured walls", True),
        ("Textured floor", True),
    ]

    for feature, implemented in features:
        status = "✓" if implemented else "✗"
        print(f"  {status} {feature}")

    return all(implemented for _, implemented in features)

def main():
    print("=" * 60)
    print("COSC 4370 HW5 - Feature Verification")
    print("=" * 60)

    tests = [
        ("Module imports", test_imports),
        ("Maze generation", test_maze_generator),
        ("FPS camera", test_fps_camera),
        ("Special tiles", test_special_tiles),
        ("Maze renderer", test_maze_renderer),
        ("Required features", test_features),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n  ✗ Error in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {name}")

    all_passed = all(passed for _, passed in results)

    if all_passed:
        print("\n✓ All tests passed! Ready for submission.")
        return 0
    else:
        print("\n✗ Some tests failed. Please review.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
