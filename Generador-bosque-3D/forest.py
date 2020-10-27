# coding=utf-8
"""
Alexander Cuevas, CC3501, 2020-1
Creates a forest made up of low poly trees and exports it as an .obj file
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

import tree


# Constants that define the size of the map, from 0 towards a cardinal direction
# meaning that MAP_X_SIZE = 10 limits the map to x = -10 and x = 10
MAP_X_SIZE = 4
MAP_Y_SIZE = 4


# Processing the parameters and name given for the .obj model
# If something isn't provided as it should, the program will try to fix it
systemArg = sys.argv

fullName = systemArg[1] if len(systemArg) > 1 else "unnamed.obj"
dotIdx = fullName.find(".")

NAME = fullName[:dotIdx]
EXTENSION = fullName[dotIdx:]

if not NAME.isidentifier():
    print("Invalid name, \"unnamed\" will be used.")
    NAME = "unnamed"

if not EXTENSION == ".obj":
    print("Invalid extension, \".obj\" will be used.")
    EXTENSION = ".obj"

preGaussian = systemArg[2] if len(systemArg) > 2 else "7"
GAUSSIAN = int(preGaussian) if preGaussian.isdecimal() else 7

preS = systemArg[3] if len(systemArg) > 3 else "3"
S = int(preS) if preS.isdecimal() else 3

preRandom = systemArg[4] if len(systemArg) > 4 else "0"
RANDOM = int(preRandom) if preRandom.isdecimal() else 0

preOrder = systemArg[5] if len(systemArg) > 5 else "2"
ORDER = int(preOrder) if preOrder.isdecimal() else 2

preDensity = systemArg[6] if len(systemArg) > 6 else "1.0"
try:
    DENSITY = float(preDensity)
except:
    DENSITY = 1.0

COMPLEXITY = 4


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


# Calculates a z value using a gaussian function
def gaussianFunction(x, y, s, sigma, mu):

    base = s * (1 / (sigma * np.sqrt(2 * np.pi)))

    exponent = (-1 / (2 * sigma ** 2)) * ((x - mu[0]) ** 2 + (y - mu[1]) ** 2)

    return base * np.exp(exponent)


# Returns a color affected by altitude (z value)
def altitudeColor(z):

    # Base colors
    bronzeii = np.array([0.65, 0.49, 0.24])
    yellowGreen = np.array([0.60, 0.80, 0.20])
    forestGreen = np.array([0.13, 0.55, 0.13])

    # Returns a dirtier color below 0
    if z <= 0:
        z = min(1, abs(z)) / 1
        return bronzeii * z + yellowGreen * (1 - z)
    
    # Returns a greener color above 0
    z = min(1, z) / 1
    return forestGreen * z + yellowGreen * (1 - z)


# Returns a normal vertex using the z value of surrounding vertices
def terrainNormal(x, y, zs, i, j):
    
    zUp = zs[i - 1, j] if i > 0 else zs[i, j]
    zDown = zs[i + 1, j] if i < x - 1 else zs[i, j]
    zLeft = zs[i, j - 1] if j > 0 else zs[i, j]
    zRight = zs[i, j + 1] if j < y - 1 else zs[i, j]

    # Creating a small plane in order to calculate a normal
    firstVextex = [4 * MAP_X_SIZE / x, 0, zDown - zUp]
    secondVextex = [0, 4 * MAP_Y_SIZE / y, zRight - zLeft]

    # Note that (4 * MAP_X_SIZE / x) represents the horizontal
    # distance between the 2 z values of interest

    return list(np.cross(firstVextex, secondVextex))


# Creates the rules for a tree using randomness
def treeRule(order = 1):

    rule = "F"

    # Branch position
    branch = ["[RF]", "[LF]", "[RUUF]", "[LDDF]", "[RDF][LUF]", "[RDDF][LUUF]"]
    branch += ["[RDDF[RUUF]F]", "[LUUF[LDDF]F]", "[RF[LUF]F]", "[LF[RDF]F]"]

    for _ in range(max(1, COMPLEXITY - order * 2)):
        randint = int(np.random.randint(0, len(branch)))
        rule += branch[randint] + "F"

    return rule


# Creates a forest with happy little trees to be put above a terrain
# Order was considered as a parameter, but it was replaced by complexity due to his cost
def plantTrees(zMap, density = 1, order = 1):

    # Graph that will contain all the trees
    forestGraph = sg.SceneGraphNode("forest")

    xSize = zMap.shape[0]
    ySize = zMap.shape[1]

    dx = 2 * MAP_X_SIZE / xSize
    dy = 2 * MAP_Y_SIZE / ySize

    x = -MAP_X_SIZE + dx / 2

    # Choosing where to plant trees
    treeCoordinates = np.random.randint(0, 40 / density, zMap.shape)

    # Plants a tree in a (x, y, z) position
    for i in range(zMap.shape[0]):

        y = -MAP_Y_SIZE + dy / 2

        for j in range(zMap.shape[1]):

            if treeCoordinates[i, j] == 0:

                # Burying the tree a little to ensure it isn't floating
                normal = terrainNormal(xSize, ySize, zMap, i, j)
                correction = (abs(normal[0]) + abs(normal[1])) / 5
                
                # Randomizing the order, size and skip parameters
                np.random.seed(RANDOM + i * j)
                variance = np.random.uniform()
                realOrder = max(1, ORDER - int(variance > 0.4))
                realSize = tree.SIZE + 0.4 * int(variance > 0.6) + 0.2 * int(variance > 0.8)
                realSize += (realOrder - 1) * 0.5
                realSkip = np.random.randint(0, realOrder**2 + 1)

                # Randomizing the rule of creation
                realRule = treeRule(realOrder)

                # Trees can't be planted close to each other
                for k in range(i, i + int(realSize + realOrder)):
                    for l in range(j, j + int(realSize + realOrder)):
                        try:
                            treeCoordinates[k, l] = 1
                        except:
                            pass

                treeGraph = tree.createTree(realRule, realOrder, realSize, realSkip)
                treeGraph.transform = tr.translate(x, y, zMap[i, j] - correction)

                forestGraph.childs += [treeGraph]
            
            y += dy
        x += dx

    return forestGraph


# Generates terrain using gaussian functions
def generateTerrain(xs, ys, s):

    verticesList = []

    vertices = []
    indices = []

    xSize = len(xs)
    ySize = len(ys)

    zs = np.zeros((xSize, ySize))

    muList = []
    sigmaList = []
    signList = []

    # Each gaussian function is randomized
    for i in range(GAUSSIAN):

        np.random.seed(RANDOM + i)
        random = 2 * np.random.uniform(0, 1.0, 2) - 1.0
        random[0] *= MAP_X_SIZE
        random[1] *= MAP_Y_SIZE

        muList += [np.copy(random)]
        
        sigmaList += [max(1, s - np.random.uniform())]
        signList += [1] if np.random.uniform() > 0.3 else [-1]

    # Generating a vertex for each sample x, y, z, using a
    # number of gaussian functions defined as a parameter
    for i in range(xSize):
        for j in range(ySize):
            x = xs[i]
            y = ys[j]
            z = 0

            for sigma, mu, sign in zip(sigmaList, muList, signList):
                z += gaussianFunction(x, y, s, sigma, mu) * sign

            zs[i, j] = z

            verticesList += [[x, y, z] + list(altitudeColor(z))]
    
    # Generating the normal vertices
    for i in range(xSize):
        for j in range(ySize):
            normal = terrainNormal(xSize, ySize, zs, i, j)

            verticesList[i * xSize + j] += normal

            vertices += verticesList[i * xSize + j]
    
    # The previous loops generates full columns j-y and then move to
    # the next i-x. Hence, the index for each vertex i,j can be computed as
    index = lambda i, j: i*len(ys) + j 
    
    # We generate quads for each cell connecting 4 neighbor vertices
    for i in range(len(xs)-1):
        for j in range(len(ys)-1):

            # Getting indices for all vertices in this quad
            isw = index(i,j)
            ise = index(i+1,j)
            ine = index(i+1,j+1)
            inw = index(i,j+1)

            # Adding this cell's quad as 2 triangles
            indices += [
                isw, ise, ine,
                ine, inw, isw
            ]

    return bs.Shape(vertices, indices), zs


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


# Exports a given forest to .obj, using the documentation in formats.pdf
def exportForest(forest):

    # File with the given name
    newFile = open(NAME + EXTENSION,"w")

    newFile.write("# 3D Forest\n")
    tree.exportGraphHelper(newFile, forest)


# Draws a given map using a pipeline
def drawMap(map, pipeline):

    # Object is barely visible at only ambient and brighter for the diffuse component.
    glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "Ka"), 0.3, 0.3, 0.3)
    glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "Kd"), 0.5, 0.5, 0.5)
    glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "Ks"), 0.1, 0.1, 0.1)

    # The map shouldn't be that shiny
    glUniform1ui(glGetUniformLocation(pipeline.shaderProgram, "shininess"), 1)

    # Drawing the shapes
    sg.drawSceneGraphNode(map, pipeline, "model")


# Main function
if __name__ == "__main__":

    # Initialize glfw
    if not glfw.init():
        sys.exit()

    width = 600
    height = 600

    window = glfw.create_window(width, height, "Forest", None, None)

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

    # Generate a terrain with 80 samples between the limits of the map
    xs = np.ogrid[-MAP_X_SIZE:MAP_X_SIZE:40j]
    ys = np.ogrid[-MAP_Y_SIZE:MAP_Y_SIZE:40j]

    terrainShape, zs = generateTerrain(xs, ys, S)

    # Creating the scene graph
    terrainGraph = sg.SceneGraphNode("terrain")
    terrainGraph.childs += [es.toGPUShape(terrainShape)]

    forestGraph = sg.SceneGraphNode("forest")
    forestGraph.childs += [terrainGraph, plantTrees(zs, DENSITY, 1)]

    if EXTENSION == ".obj":
        exportForest(forestGraph)

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
        glUniform1f(glGetUniformLocation(lightingPipeline.shaderProgram, "quadraticAttenuation"), 0.002)

        # Finishing the lighting configuration, the "sun" is always located above one corner of the map
        glUniform3f(glGetUniformLocation(lightingPipeline.shaderProgram, "lightPosition"), MAP_X_SIZE, MAP_Y_SIZE, 10)
        glUniform3f(glGetUniformLocation(lightingPipeline.shaderProgram, "viewPosition"), viewPos[0], viewPos[1], viewPos[2])

        # Drawing the shapes according to material properties
        drawMap(forestGraph, lightingPipeline)

        # Once the drawing is rendered, buffers are swap so an uncomplete drawing is never seen.
        glfw.swap_buffers(window)

    glfw.terminate()