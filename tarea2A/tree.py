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
        self.showAxis = True
        self.cameraZoom = 3
        self.cameraPhi = 45
        self.cameraTheta = 45


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

    elif action != glfw.PRESS:
        return
    
    elif key == glfw.KEY_LEFT_CONTROL:
        controller.showAxis = not controller.showAxis

    elif key == glfw.KEY_SPACE:
        controller.fillPolygon = not controller.fillPolygon

    elif key == glfw.KEY_ESCAPE:
        sys.exit()


# Creates a branch or tree trunk of variable length
# Ratio: Size of the bases of the shape in proportion to the lenght
# Sides: How many sides are used to create the bases of the shape,
# must be greater than 2
def createBranch(length = 1.0, ratio = 0.1, sides = 6):

    radius = length * ratio
    angle = 360 / sides

    colorCoffee = [0.67, 0.33, 0.0]

    vertices = []
    indices = []

    # Creating vertices that will become the center of two polygons
    # The normals of all vertices were set up considering each branch as
    # a component of a tree, so some simplifications were be made
    vertices += [0, 0, length] + colorCoffee + [0, 0, 1]
    vertices += [0, 0, 0] + colorCoffee + [0, 0, -1]

    # Creating a prism made up of two connected polygons
    for i in range(sides):

        sub_angle = angle * i * np.pi / 180

        x = radius * np.cos(sub_angle)
        y = radius * np.sin(sub_angle)

        vertices += [x, y, length] + colorCoffee + [x, y, 0]
        vertices += [x, y, 0] + colorCoffee + [x, y, 0]

        if i > 0:
            j = (i + 1) * 2

            # Creating the lower and upper base of the prism
            indices += [0, j - 2, j]
            indices += [1, j - 1, j + 1]

            # Creating the vertical faces of the prism
            indices += [j + 1, j - 1, j - 2]
            indices += [j - 2, j, j + 1]
    

    lastIdx = sides * 2

    # Closing the lower and upper base
    indices += [0, 2, lastIdx]
    indices += [1, 3, lastIdx + 1]

    # Closing the vertical faces
    indices += [lastIdx + 1, 3, 2]
    indices += [lastIdx, lastIdx + 1, 2]

    return bs.Shape(vertices, indices)


# Creates a tree using a rule of generation and order of iterations
def createTree(order = 1, rule = "F[RF]F[LF]F", length = 1.0):

    treeGraph = sg.SceneGraphNode("tree")

    blueprint = "F"

    for i in range(order):
        newBlueprint = ""

        for character in blueprint:
            newBlueprint += rule if character == "F" else character
        
        blueprint = newBlueprint
        length /= 3

    angleList = [0]
    zList = [0]
    xList = [0]

    for character in blueprint:
        if character == "F":

            angle = angleList[-1]
            z = zList[-1]
            x = xList[-1]

            gpuBranch = es.toGPUShape(createBranch(length, 0.05))

            branchGraph = sg.SceneGraphNode("branch")
            branchGraph.childs += [gpuBranch]
            branchGraph.transform = tr.matmul([tr.translate(x, 0, z), tr.rotationY(angle)])

            treeGraph.childs += [branchGraph]

            zList[-1] += length * np.cos(angleList[-1])
            xList[-1] += length * np.sin(angleList[-1])
        
        elif character == "L":
            angleList[-1] += -27 * np.pi / 180

        elif character == "R":
            angleList[-1] += 27 * np.pi / 180
        
        elif character == "[":
            angleList += [angleList[-1]]
            zList += [zList[-1]]
            xList += [xList[-1]]
        
        elif character == "]":
            angleList.pop()
            zList.pop()
            xList.pop()

    return treeGraph


# Moves the camera around a sphere looking at the center,
# returns the view matrix and the viewPos vector for later use
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

    return tr.lookAt(viewPos, np.array([0, 0, 0.5]), viewUp), viewPos


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

    # Shader programs, the first without lighting and the second with Phong lighting
    colorPipeline = es.SimpleModelViewProjectionShaderProgram()
    lightingPipeline = ls.SimplePhongShaderProgram()

    glUseProgram(colorPipeline.shaderProgram)

    # Setting up the clear screen color
    glClearColor(0.85, 0.85, 0.85, 1.0)

    # As we work in 3D, we need to check which part is in front,
    # and which one is at the back
    glEnable(GL_DEPTH_TEST)

    # Creating shapes on GPU memory
    gpuAxis = es.toGPUShape(bs.createAxis())
    treeGraph = createTree(3)

    # Setting up the projection
    projection = tr.perspective(45, float(width)/float(height), 0.1, 100)

    while not glfw.window_should_close(window):

        # Using GLFW to check for input events
        glfw.poll_events()

        # Moving the camera
        view, viewPos = moveCamera()

        # Clearing the screen in both, color and depth
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Filling or not the shapes depending on the controller state
        if (controller.fillPolygon):
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

        # The axis is drawn without lighting effects
        if controller.showAxis:
            glUseProgram(colorPipeline.shaderProgram)
            glUniformMatrix4fv(glGetUniformLocation(colorPipeline.shaderProgram, "projection"), 1, GL_TRUE, projection)
            glUniformMatrix4fv(glGetUniformLocation(colorPipeline.shaderProgram, "view"), 1, GL_TRUE, view)
            glUniformMatrix4fv(glGetUniformLocation(colorPipeline.shaderProgram, "model"), 1, GL_TRUE, tr.identity())
            colorPipeline.drawShape(gpuAxis, GL_LINES)
        
        # Using the lighting shader program
        glUseProgram(lightingPipeline.shaderProgram)

        # Setting all uniform shader variables
        
        # White light in all components: ambient, diffuse and specular.
        glUniform3f(glGetUniformLocation(lightingPipeline.shaderProgram, "La"), 1.0, 1.0, 1.0)
        glUniform3f(glGetUniformLocation(lightingPipeline.shaderProgram, "Ld"), 1.0, 1.0, 1.0)
        glUniform3f(glGetUniformLocation(lightingPipeline.shaderProgram, "Ls"), 1.0, 1.0, 1.0)

        # Object is barely visible at only ambient and brighter for the diffuse component.
        glUniform3f(glGetUniformLocation(lightingPipeline.shaderProgram, "Ka"), 0.3, 0.3, 0.3)
        glUniform3f(glGetUniformLocation(lightingPipeline.shaderProgram, "Kd"), 0.5, 0.5, 0.5)
        glUniform3f(glGetUniformLocation(lightingPipeline.shaderProgram, "Ks"), 0.1, 0.1, 0.1)

        glUniform3f(glGetUniformLocation(lightingPipeline.shaderProgram, "lightPosition"), 5, 5, 5)
        glUniform3f(glGetUniformLocation(lightingPipeline.shaderProgram, "viewPosition"), viewPos[0], viewPos[1], viewPos[2])

        # In my humble opinion, natural wood isn't shiny at all
        glUniform1ui(glGetUniformLocation(lightingPipeline.shaderProgram, "shininess"), 1)

        # Finishing the lighting configuration
        glUniform1f(glGetUniformLocation(lightingPipeline.shaderProgram, "constantAttenuation"), 0.0001)
        glUniform1f(glGetUniformLocation(lightingPipeline.shaderProgram, "linearAttenuation"), 0.03)
        glUniform1f(glGetUniformLocation(lightingPipeline.shaderProgram, "quadraticAttenuation"), 0.01)

        glUniformMatrix4fv(glGetUniformLocation(lightingPipeline.shaderProgram, "projection"), 1, GL_TRUE, projection)
        glUniformMatrix4fv(glGetUniformLocation(lightingPipeline.shaderProgram, "view"), 1, GL_TRUE, view)
        glUniformMatrix4fv(glGetUniformLocation(lightingPipeline.shaderProgram, "model"), 1, GL_TRUE, tr.identity())

        # Drawing the shapes
        sg.drawSceneGraphNode(treeGraph, lightingPipeline, "model")

        # Once the drawing is rendered, buffers are swap so an uncomplete drawing is never seen.
        glfw.swap_buffers(window)

    glfw.terminate()
