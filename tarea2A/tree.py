# coding=utf-8
"""
Alexander Cuevas, CC3501, 2020-1
Work in progress, will become a tree
"""

import glfw
from OpenGL.GL import *
import OpenGL.GL.shaders
import numpy as np
import sys

import transformations as tr
import basic_shapes as bs
import easy_shaders as es
import scene_graph as sg
import lighting_shaders as ls


# Processing the parameters and name given for the .obj model
systemArg = sys.argv

fullName = systemArg[0]
dotIdx = fullName.find(".")

name = fullName[:dotIdx]
extension = fullName[dotIdx:]


# A class to store the application control
class Controller:
    def __init__(self):
        self.fillPolygon = True
        self.cameraZoom = 10
        self.cameraPhi = 0
        self.cameraTheta = 0


# Global controller that will communicate with the callback function
controller = Controller()


def on_key(window, key, scancode, action, mods):

    global controller

    if key == glfw.KEY_UP:
        controller.cameraPhi += 0.1
    
    elif key == glfw.KEY_DOWN:
        controller.cameraPhi -= 0.1
    
    elif key == glfw.KEY_RIGHT:
        controller.cameraTheta += 0.1
    
    elif key == glfw.KEY_LEFT:
        controller.cameraTheta -= 0.1
    
    elif key == glfw.KEY_S:
        controller.cameraZoom += 0.1
    
    elif key == glfw.KEY_W:
        controller.cameraZoom = max(1.0, controller.cameraZoom - 0.1)

    if action != glfw.PRESS:
        return

    elif key == glfw.KEY_SPACE:
        controller.fillPolygon = not controller.fillPolygon

    elif key == glfw.KEY_ESCAPE:
        sys.exit()


# Creates a branch or tree trunk of variable length
# Ratio: Size of the bases of the shape in proportion to the lenght
# Complexity: How many sides are used to create the bases of the shape,
# must be greater than 2
def createBranch(length = 1.0, ratio = 0.1, complexity = 6):

    halfLenght = length / 2
    radius = length * ratio

    angle = 360 / complexity

    colorCoffee = [0.67, 0.33, 0.0]

    vertices = []
    indices = []

    # Creating vertices that will become the center of two polygons
    vertices += [0, 0, halfLenght] + colorCoffee
    vertices += [0, 0, -halfLenght] + colorCoffee

    # Creating a prism made up of two connected polygons
    for i in range(complexity):

        sub_angle = angle * i * np.pi / 180

        x = radius * np.cos(sub_angle)
        y = radius * np.sin(sub_angle)

        vertices += [x, y, halfLenght] + colorCoffee
        vertices += [x, y, -halfLenght] + colorCoffee

        if i > 0:
            j = (i + 1) * 2

            # Creating the lower and upper base of the prism
            indices += [0, j - 2, j]
            indices += [1, j - 1, j + 1]

            # Creating the vertical faces of the prism
            indices += [j + 1, j - 1, j - 2]
            indices += [j - 2, j, j + 1]
    

    lastIdx = complexity * 2

    # Closing the lower and upper base
    indices += [0, 2, lastIdx]
    indices += [1, 3, lastIdx + 1]

    # Closing the vertical faces
    indices += [lastIdx + 1, 3, 2]
    indices += [lastIdx, lastIdx + 1, 2]

    return bs.Shape(vertices, indices)


# Moves the camera around a sphere looking at the center,
# returns a view matrix
def moveCamera():

    # Angles of a spheric system, determined by the controller
    phi = controller.cameraPhi
    theta = controller.cameraTheta

    # Zoom level of the camera, how far is from the center
    zoom = controller.cameraZoom

    # Camera position in cartesian coordinates
    camX = zoom * np.sin(phi) * np.cos(theta)
    camY = zoom * np.sin(phi) * np.sin(theta)
    camZ = zoom * np.cos(phi)

    # Phi direction in cartesian coordinates
    upX = -np.cos(phi) * np.cos(theta)
    upY = -np.cos(phi) * np.sin(theta)
    upZ = np.sin(phi)

    viewPos = np.array([camX, camY, camZ])
    viewUp = np.array([upX, upY, upZ])

    return tr.lookAt(viewPos, np.array([0,0,0]), viewUp)


if __name__ == "__main__":

    # Initialize glfw
    if not glfw.init():
        sys.exit()

    width = 600
    height = 600

    window = glfw.create_window(width, height, "Invisible tree", None, None)

    if not window:
        glfw.terminate()
        sys.exit()

    glfw.make_context_current(window)

    # Connecting the callback function 'on_key' to handle keyboard events
    glfw.set_key_callback(window, on_key)

    # This shader program does not consider lighting
    colorPipeline = es.SimpleModelViewProjectionShaderProgram()

    glUseProgram(colorPipeline.shaderProgram)

    # Setting up the clear screen color
    glClearColor(0.85, 0.85, 0.85, 1.0)

    # As we work in 3D, we need to check which part is in front,
    # and which one is at the back
    glEnable(GL_DEPTH_TEST)

    # Creating shapes on GPU memory
    gpuPolygon = es.toGPUShape(createBranch(1.0, 0.1, 3))
    gpuAxis = es.toGPUShape(bs.createAxis(4))

    while not glfw.window_should_close(window):

        # Using GLFW to check for input events
        glfw.poll_events()

        projection = tr.perspective(45, float(width)/float(height), 0.1, 100)

        # Moving the camera
        view = moveCamera()

        # Clearing the screen in both, color and depth
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Filling or not the shapes depending on the controller state
        if (controller.fillPolygon):
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    
        glUniformMatrix4fv(glGetUniformLocation(colorPipeline.shaderProgram, "projection"), 1, GL_TRUE, projection)
        glUniformMatrix4fv(glGetUniformLocation(colorPipeline.shaderProgram, "view"), 1, GL_TRUE, view)
        glUniformMatrix4fv(glGetUniformLocation(colorPipeline.shaderProgram, "model"), 1, GL_TRUE, tr.identity())

        colorPipeline.drawShape(gpuPolygon)
        colorPipeline.drawShape(gpuAxis, GL_LINES)

        # Once the drawing is rendered, buffers are swap so an uncomplete drawing is never seen.
        glfw.swap_buffers(window)

    glfw.terminate()
