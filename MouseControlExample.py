import pygame
from pygame.locals import *

from OpenGL.GL import *
from OpenGL.GLU import *

import math

def verts(x, y, z, n):
    vertices = (
        (1+(2*x), -1+(2*y), -1+(2*z)),
        (1+(2*x), 1+(2*y), -1+(2*z)),
        (-1+(2*x), 1+(2*y), -1+(2*z)),
        (-1+(2*x), -1+(2*y), -1+(2*z)),
        (1+(2*x), -1+(2*y), 1+(2*z)),
        (1+(2*x), 1+(2*y), 1+(2*z)),
        (-1+(2*x), -1+(2*y), 1+(2*z)),
        (-1+(2*x), 1+(2*y), 1+(2*z))
        )
    return(vertices)


edges = (
    (0,1),
    (0,3),
    (0,4),
    (2,1),
    (2,3),
    (2,7),
    (6,3),
    (6,4),
    (6,7),
    (5,1),
    (5,4),
    (5,7)
    )

colors = (
    (1,0,0),
    (0,1,0),
    (0,0,1),
    (0,1,0),
    (1,1,1),
    (0,1,1),
    (1,0,0),
    (0,1,0),
    (0,0,1),
    (1,0,0),
    (1,1,1),
    (0,1,1),
    )

surfaces = (
    (0,1,2,3),
    (3,2,7,6),
    (6,7,5,4),
    (4,5,1,0),
    (1,5,7,2),
    (4,0,3,6)
    )


forced = False
def Cube(vx,vy,vz):
    glBegin(GL_QUADS)
    for x,surface in enumerate(surfaces):
        for vertex in surface:
            x+=1
            glColor3fv(colors[x])
            glVertex3fv(verts(vx,vy,vz,1)[vertex])
    glEnd()


    glBegin(GL_LINES)
    for edge in edges:
        for vertex in edge:
            glVertex3fv(verts(vx,vy,vz,1)[vertex])
    glEnd()



pygame.init()
display = (800, 800)
scree = pygame.display.set_mode(display, DOUBLEBUF | OPENGL)


glEnable(GL_DEPTH_TEST)
glEnable(GL_LIGHTING)
glShadeModel(GL_SMOOTH)
glEnable(GL_COLOR_MATERIAL)
glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

glEnable(GL_LIGHT0)
glLightfv(GL_LIGHT0, GL_AMBIENT, [0.5, 0.5, 0.5, 1])
glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1])


sphere = gluNewQuadric() 

glMatrixMode(GL_PROJECTION)
gluPerspective(45, (display[0]/display[1]), 0.1, 50.0)

glMatrixMode(GL_MODELVIEW)
gluLookAt(0, -8, 0, 0, 0, 0, 0, 0, 1)
viewMatrix = glGetFloatv(GL_MODELVIEW_MATRIX)
glLoadIdentity()

# init mouse movement and center mouse on screen
displayCenter = [scree.get_size()[i] // 2 for i in range(2)]
mouseMove = [0, 0]
pygame.mouse.set_pos(displayCenter)

up_down_angle = 0.0
run = True

glColor(1,1,1,1)
while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                run = False
            if event.key == pygame.K_PAUSE or event.key == pygame.K_p:
                paused = not paused
                pygame.mouse.set_pos(displayCenter) 
        if event.type == pygame.MOUSEMOTION:
            mouseMove = [event.pos[i] - displayCenter[i] for i in range(2)]
        pygame.mouse.set_pos(displayCenter)    

    # get keys
    keypress = pygame.key.get_pressed()
    #mouseMove = pygame.mouse.get_rel()

    # init model view matrix
    glLoadIdentity()

    # apply the look up and down
    up_down_angle += mouseMove[1]*0.1
    glRotatef(up_down_angle, 1.0, 0.0, 0.0)

    # init the view matrix
    glPushMatrix()
    glLoadIdentity()

    # apply the movment 
    if keypress[pygame.K_w]:
        glTranslatef(0,0,0.1)
    if keypress[pygame.K_s]:
        glTranslatef(0,0,-0.1)
    if keypress[pygame.K_d]:
        glTranslatef(-0.1,0,0)
    if keypress[pygame.K_a]:
        glTranslatef(0.1,0,0)
    if keypress[pygame.K_LSHIFT]:
        glTranslatef(0,0.5,0)
    if keypress[pygame.K_SPACE]:
        glTranslatef(0,-0.5,0)

    # apply the left and right rotation
    glRotatef(mouseMove[0]*0.1, 0.0, 1.0, 0.0)

    # multiply the current matrix by the get the new view matrix and store the final vie matrix 
    glMultMatrixf(viewMatrix)
    viewMatrix = glGetFloatv(GL_MODELVIEW_MATRIX)

    # apply view matrix
    glPopMatrix()
    glMultMatrixf(viewMatrix)

    #glLightfv(GL_LIGHT0, GL_POSITION, [1, -1, 1, 0])

    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

    glPushMatrix()
    glColor(1,1,1,1)


    Cube(0,0,0)
    Cube(1,0,0)
    Cube(0,1,0)
    Cube(0,0,1)
    Cube(-2,0,0)

    glColor4f(0.5, 0.5, 0.5, 1)
    glBegin(GL_QUADS)
    glVertex3f(-10, -10, -2)
    glVertex3f(10, -10, -2)
    glVertex3f(10, 10, -2)
    glVertex3f(-10, 10, -2)
    glEnd()

    glTranslatef(-1.5, 0, 0)
    glColor4f(0.5, 0.2, 0.2, 1)
    gluSphere(sphere, 1.0, 32, 16)

    glTranslatef(3, 0, 0)
    glColor4f(0.2, 0.2, 0.5, 1)
    gluSphere(sphere, 1.0, 32, 16) 

    glPopMatrix()

    pygame.display.flip()
    pygame.time.wait(10)

pygame.quit()