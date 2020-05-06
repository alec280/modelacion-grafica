# coding=utf-8
"""
Alexander Cuevas, CC3501, 2020-1
Creates a low poly tree
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


# Constant used in the creation of brances
BRANCH_ANGLE = 27 * np.pi / 180


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
        self.cameraZoom = 2
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


# Creates a regular dodecahedron, the green channel can be modified
def createDodecahedron(g = 0.4):

    # The golden ratio and its inverse
    gRa = (1 + np.sqrt(5)) / 2
    iRa = 1 / gRa

    # Defining the location and colors of each vertex  of the shape
    vertices = [
            #    positions        colors          normals
             iRa,  gRa,  0.0, 0.0, g, 0.0,  iRa,  gRa,  0.0,
             gRa,  0.0,  iRa, 0.0, g, 0.0,  gRa,  0.0,  iRa,
             1.0,  1.0,  1.0, 0.0, g, 0.0,  1.0,  1.0,  1.0,
             gRa,  0.0, -iRa, 0.0, g, 0.0,  gRa,  0.0, -iRa,
             1.0,  1.0, -1.0, 0.0, g, 0.0,  1.0,  1.0, -1.0,
             1.0, -1.0,  1.0, 0.0, g, 0.0,  1.0, -1.0,  1.0,
             iRa, -gRa,  0.0, 0.0, g, 0.0,  iRa, -gRa,  0.0,
             1.0, -1.0, -1.0, 0.0, g, 0.0,  1.0, -1.0, -1.0,
             0.0, -iRa, -gRa, 0.0, g, 0.0,  0.0, -iRa, -gRa,
             0.0,  iRa, -gRa, 0.0, g, 0.0,  0.0,  iRa, -gRa,
            -1.0, -1.0, -1.0, 0.0, g, 0.0, -1.0, -1.0, -1.0,
            -iRa, -gRa,  0.0, 0.0, g, 0.0, -iRa, -gRa,  0.0,
            -1.0,  1.0, -1.0, 0.0, g, 0.0, -1.0,  1.0, -1.0,
            -gRa,  0.0, -iRa, 0.0, g, 0.0, -gRa,  0.0, -iRa,
            -iRa,  gRa,  0.0, 0.0, g, 0.0, -iRa,  gRa,  0.0,
             0.0,  iRa,  gRa, 0.0, g, 0.0,  0.0,  iRa,  gRa,
            -1.0,  1.0,  1.0, 0.0, g, 0.0,  1.0,  1.0, -1.0,
            -1.0, -1.0,  1.0, 0.0, g, 0.0, -1.0, -1.0,  1.0,
            -gRa,  0.0,  iRa, 0.0, g, 0.0, -gRa,  0.0,  iRa,
             0.0, -iRa,  gRa, 0.0, g, 0.0,  0.0, -iRa,  gRa]
    
    # Defining connections among vertices
    # We have a triangle every 3 indices specified
    indices = [0,  1,  2,  0,  3,  1,  0,  4,  3,  9,  3,  4,
               9,  7,  3,  9,  8,  7, 11,  7,  6, 11,  8,  7,
              11, 10,  8,  6,  1,  5,  6,  3,  1,  6,  7,  3,
              12,  0, 14, 12,  4,  0, 12,  9,  4, 10, 12, 13,
              10,  9, 12, 10,  8,  9, 17, 13, 18, 17, 10, 13,
              17, 11, 10, 16,  2, 15, 16,  0,  2, 16, 14,  0,
              18, 14, 16, 18, 12, 14, 18, 13, 12, 19,  2, 15,
              19,  1,  2, 19,  5,  1, 17,  5, 19, 17,  6,  5,
              17, 11,  6, 18, 15, 16, 18, 19, 15, 18, 17, 19]

    return bs.Shape(vertices, indices)


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


# Creates a dodecahedron of a certain size and green coloration to
# be used as leaves for a tree, it returns a scene graph
def createLeaf(size = 0.2, green = 0.4):

    # Scene graph that will contain the scaled leaf
    scaledLeafGraph = sg.SceneGraphNode("scaledLeaf")
    scaledLeafGraph.transform = tr.uniformScale(size)
    scaledLeafGraph.childs += [es.toGPUShape(createDodecahedron(green))]

    # Final scene graph
    leafGraph = sg.SceneGraphNode("leaf")
    leafGraph.childs += [scaledLeafGraph]

    return leafGraph



# Creates a tree using a rule of generation, order of iterations and size
# There is also decay, which affects the size of branches as their distance
# with the tree trunk increases
def createTree(order = 1, rule = "F[RF]F[LF]F", size = 1.0):

    # The different parts of the tree with different materials
    woodGraph = sg.SceneGraphNode("wood")
    leavesGraph = sg.SceneGraphNode("leaf")

    # Scene graph that will contain the whole tree
    treeGraph = sg.SceneGraphNode("tree")
    treeGraph.childs += [woodGraph, leavesGraph]

    # String used to construct the tree
    blueprint = "F"
    counter = 0
    lockCounter = 0

    # Applies the rule to the blueprint, increasing the complexity
    for _ in range(order):
        newBlueprint = ""

        for character in blueprint:
            newBlueprint += rule if character == "F" else character
        
        blueprint = newBlueprint
    
    blueprint += "]"
    
    # Counts how many times the rule is applied, reducing the size of the
    # branches in order to make a tree of the given size
    for character in rule:

        if character == "F" and lockCounter == 0:
            counter += 1
        
        elif character == "[":
            lockCounter += 1
        
        elif character == "]":
            lockCounter -= 1

    size /= counter ** order

    # Lists that store the information necessary to put new branches
    phiList = [0]
    thetaList = [0]
    decayList = [0.8]
    xList = [0]
    yList = [0]
    zList = [0]

    allLists = [phiList, thetaList, decayList, xList, yList, zList]

    # Creating the tree
    for character in blueprint:

        # Creating a new branch considering the lists of properties
        if character == "F":

            phi = phiList[-1]
            theta = thetaList[-1]
            decay = decayList[-1]
            x = xList[-1]
            y = yList[-1]
            z = zList[-1]

            # Adding the model to the tree graph
            gpuBranch = es.toGPUShape(createBranch(size, 0.05))

            # Adding the wood
            branchGraph = sg.SceneGraphNode("branch")
            branchGraph.childs += [gpuBranch]

            rotation = tr.matmul([tr.rotationZ(theta), tr.rotationY(phi)])

            branchGraph.transform = tr.matmul([rotation, tr.uniformScale(decay)])
            branchGraph.transform = tr.matmul([tr.translate(x, y, z), branchGraph.transform])

            woodGraph.childs += [branchGraph]

            # Changing the position of the next branch
            localSize = size * decay

            xList[-1] += localSize * np.sin(phi) * np.cos(theta)
            yList[-1] += localSize * np.sin(phi) * np.sin(theta)
            zList[-1] += localSize * np.cos(phi)
        
        # Changing the angle of the next branch using a spherical system
        elif character == "R":
            phiList[-1] += BRANCH_ANGLE

        elif character == "L":
            phiList[-1] -= BRANCH_ANGLE
        
        elif character == "U":
            thetaList[-1] += BRANCH_ANGLE
        
        elif character == "D":
            thetaList[-1] -= BRANCH_ANGLE
        
        # Setting up a new path for the branches
        elif character == "[":
            for ls in allLists:
                ls.append(ls[-1])

            decayList[-1] **= 2
        
        # Closing a path, sometimes with a leaf
        elif character == "]":

            x = xList[-1]
            y = yList[-1]
            z = zList[-1]

            # Adding a leaf at the end of a path
            leafGraph = createLeaf(0.2 * size * decayList[-1])
            leafGraph.transform = tr.translate(x, y, z)

            leavesGraph.childs += [leafGraph]

            for ls in allLists:
                ls.pop()

    return treeGraph


# Moves the camera around a sphere looking at the center,
# returns the view matrix and the viewPos vector for later use
def moveCamera():

    # Angles of a spherical system, determined by the controller
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

    return tr.lookAt(viewPos, np.array([0, 0, 0.4]), viewUp), viewPos


# Draws a given tree using a pipeline
def drawTree(tree, pipeline):

    # Object is barely visible at only ambient and brighter for the diffuse component.
    glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "Ka"), 0.3, 0.3, 0.3)
    glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "Kd"), 0.5, 0.5, 0.5)
    glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "Ks"), 0.1, 0.1, 0.1)

    # In my humble opinion, natural wood isn't shiny at all
    glUniform1ui(glGetUniformLocation(pipeline.shaderProgram, "shininess"), 1)

    # Drawing the shapes
    sg.drawSceneGraphNode(tree, pipeline, "model")


# Main function
if __name__ == "__main__":

    # Initialize glfw
    if not glfw.init():
        sys.exit()

    width = 600
    height = 600

    window = glfw.create_window(width, height, "Tree", None, None)

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
    treeGraph = createTree(2, "F[URF]F[RF]F[DLF]F")

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
        glUniformMatrix4fv(glGetUniformLocation(lightingPipeline.shaderProgram, "projection"), 1, GL_TRUE, projection)
        glUniformMatrix4fv(glGetUniformLocation(lightingPipeline.shaderProgram, "view"), 1, GL_TRUE, view)
        glUniformMatrix4fv(glGetUniformLocation(lightingPipeline.shaderProgram, "model"), 1, GL_TRUE, tr.identity())

        # Setting all uniform shader variables
        
        # White light in all components: ambient, diffuse and specular
        glUniform3f(glGetUniformLocation(lightingPipeline.shaderProgram, "La"), 1.0, 1.0, 1.0)
        glUniform3f(glGetUniformLocation(lightingPipeline.shaderProgram, "Ld"), 1.0, 1.0, 1.0)
        glUniform3f(glGetUniformLocation(lightingPipeline.shaderProgram, "Ls"), 1.0, 1.0, 1.0)

        # Constants of the light
        glUniform1f(glGetUniformLocation(lightingPipeline.shaderProgram, "constantAttenuation"), 0.0001)
        glUniform1f(glGetUniformLocation(lightingPipeline.shaderProgram, "linearAttenuation"), 0.03)
        glUniform1f(glGetUniformLocation(lightingPipeline.shaderProgram, "quadraticAttenuation"), 0.01)

        # Finishing the lighting configuration
        glUniform3f(glGetUniformLocation(lightingPipeline.shaderProgram, "lightPosition"), 5, 5, 5)
        glUniform3f(glGetUniformLocation(lightingPipeline.shaderProgram, "viewPosition"), viewPos[0], viewPos[1], viewPos[2])

        # Drawing the shapes according to material properties
        drawTree(treeGraph, lightingPipeline)

        # Once the drawing is rendered, buffers are swap so an uncomplete drawing is never seen.
        glfw.swap_buffers(window)

    glfw.terminate()
