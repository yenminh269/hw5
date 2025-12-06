# -*- coding: utf-8 -*-
"""
This file will display the FPS of the game based on the pygame clock
"""

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

def draw_cube():
    glBegin(GL_QUADS)
    for surface in cube_surfaces:
        for vertex in surface:
            glVertex3fv(cube_vertices[vertex])
    glEnd()

def render_fps(clock, font):
    fps = clock.get_fps()
    fps_text = font.render(f"FPS: {fps:.2f}", True, (128, 128, 128), (0, 0, 0))
    fps_data = pygame.image.tostring(fps_text, "RGBA", True)
    glWindowPos2d(10, 10)
    glDrawPixels(fps_text.get_width(), fps_text.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, fps_data)

cube_vertices = [
    [1, 1, -1], [1, -1, -1], [-1, -1, -1], [-1, 1, -1],
    [1, 1, 1], [1, -1, 1], [-1, -1, 1], [-1, 1, 1]
]

cube_surfaces = [
    [0, 1, 2, 3], [3, 2, 6, 7], [7, 6, 5, 4],
    [4, 5, 1, 0], [1, 5, 6, 2], [4, 0, 3, 7]
]

def main():
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("OpenGL FPS Display")

    gluPerspective(45, display[0] / display[1], 0.1, 50.0)
    glTranslatef(0.0, 0.0, -5)

    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 18)

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                return

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glRotatef(1, 1, 1, 1)
        draw_cube()
        render_fps(clock, font)

        pygame.display.flip()
        clock.tick(30)

if __name__ == "__main__":
    main()