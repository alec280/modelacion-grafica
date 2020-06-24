# coding=utf-8
"""
Alexander Cuevas, CC3501, 2020-1
Visualizes the solution of a Laplace equation in a 3D space
"""

import glfw
from OpenGL.GL import *
import OpenGL.GL.shaders
import numpy as np
import json
import sys

import transformations as tr
import basic_shapes as bs
import easy_shaders as es
import scene_graph as sg
import lighting_shaders as ls


# Loads a .json file that setups the problem
if len(sys.argv) <= 1:
    print("Invalid setup data.")
    sys.exit()

name = sys.argv[1]

with open(name) as j:
    data = json.load(j)

# Loads the .npy file that solves that problem
solution_name = name[:name.index(".")] + '_solution.npy'

try:
    with open(solution_name) as s:
        print("Loading solution...")
except:
    print("Solution not found.")
    sys.exit()

solution = np.load(solution_name)
shapeSol = solution.shape

# Checks minimal and maximal values for the heat map
minval = np.min(solution[np.nonzero(solution)])
maxval = np.max(solution)
midval = (maxval + minval) / 2


# Class that stores the application control
class Controller:
    def __init__(self):
        self.fillPolygon = True
        self.cameraTheta = 45 * np.pi / 180
        self.xPos = data["L"] / 2
        self.yPos = data["P"] / 2


# Global controller that communicates with the callback function
controller = Controller()


# Helps to control the camera by snapping it to these degrees
SNAP_ANGLES = np.array([0, np.pi / 4, np.pi / 2, 3 * np.pi / 4, np.pi, 
                        5 * np.pi / 4, 3 * np.pi / 2, 7 * np.pi / 4, 2 * np.pi])


def on_key(window, key, scancode, action, mods):

    global controller
    global data

    # Moving the camera around, it will try to snap to certain angles
    if key in [glfw.KEY_UP, glfw.KEY_DOWN]:
        sign = 1 if key == glfw.KEY_UP else -1

        angle = controller.cameraTheta
        for snap in SNAP_ANGLES:
            if abs(angle - snap) < 0.1:
                controller.cameraTheta = snap % (2 * np.pi)
                break

        controller.xPos += 0.1 * sign * np.sin(controller.cameraTheta)
        controller.yPos += 0.1 * sign * np.cos(controller.cameraTheta)

        # Limits the movement to the interior of the hotel
        if controller.xPos < 0:
            controller.xPos = 0
        elif controller.xPos > 5 * data["L"] + 4 * data["W"]:
            controller.xPos = 5 * data["L"] + 4 * data["W"]
        
        if controller.yPos < 0:
            controller.yPos = 0
        elif controller.yPos > data["P"] + data["W"] + data["D"]:
            controller.yPos = data["P"] + data["W"] + data["D"]
    
    elif key == glfw.KEY_RIGHT:
        controller.cameraTheta = (controller.cameraTheta + np.pi / 90) % (2 * np.pi)
    
    elif key == glfw.KEY_LEFT:
        controller.cameraTheta = (controller.cameraTheta - np.pi / 90) % (2 * np.pi)

    elif action != glfw.PRESS:
        return
    
    elif key == glfw.KEY_SPACE:
        controller.fillPolygon = not controller.fillPolygon

    elif key == glfw.KEY_ESCAPE:
        sys.exit()


# Colorates the heat map with 3 colors
def colorMap(i, j):

    # Getting the temperature
    x = min(int(i / 0.1 + 0.0001), shapeSol[0] - 1)
    y = min(int(j / 0.1 + 0.0001), shapeSol[1] - 1)
    temperature = solution[x, y]

    colorMin = np.array([0, 0, 1])
    colorMid = np.array([1, 1, 0])
    colorMax = np.array([1, 0, 0])

    # Assigning the colors
    if minval <= temperature <= midval:
        ratio = (temperature - minval) / (midval - minval)
        return list(colorMin * (1 - ratio) + colorMid * ratio)
    else:
        ratio = (temperature - midval) / (maxval - midval)
        return list(colorMid * (1 - ratio) + colorMax * ratio)


# Returns a list of the key points of the geometry
def keyPoints():
    global data

    # Geometry of the problem
    P = data["P"]
    L = data["L"]
    D = data["D"]
    W = data["W"]
    E = data["E"]
    H1 = data["H1"]
    H2 = data["H2"]
    
    # List of points
    pts = [
        [0, 0, 0], #0
        [H1, 0, 0],
        [H1 + H2, 0, 0], 
        [5 * L + 4 * W, 0, 0], 
        [0, P, 0], 
        [L - E, P, 0], #5
        [L, P, 0], 
        [2 * L + W - E, P, 0], 
        [2 * L + W, P, 0], 
        [3 * L + 2 * W - E, P, 0], 
        [3 * L + 2 * W, P, 0], #10
        [4 * L + 3 * W - E, P, 0], 
        [4 * L + 3 * W, P, 0], 
        [5 * L + 4 * W - E, P, 0],
        [0, P + W, 0], 
        [L - E, P + W, 0], #15
        [L + W, P + W, 0], 
        [2 * L + W - E, P + W, 0], 
        [2 * (L + W), P + W, 0], 
        [3 * L + 2 * W - E, P + W, 0], 
        [3 * (L + W), P + W, 0], #20
        [4 * L + 3 * W - E, P + W, 0], 
        [4 * (L + W), P + W, 0], 
        [5 * L + 4 * W - E, P + W, 0], 
        [0, P + W + D, 0], 
        [L, P + W + D, 0], #25
        [L + W, P + W + D, 0], 
        [2 * L + W, P + W + D, 0], 
        [2 * (L + W), P + W + D, 0], 
        [3 * L + 2 * W, P + W + D, 0],
        [3 * (L + W), P + W + D, 0], #30
        [4 * L + 3 * W, P + W + D, 0], 
        [4 * (L + W), P + W + D, 0],
        [5 * L + 4 * W, P + W + D, 0]]
    
    return pts


# Shape of the floor
def createFloor():
    global data

    # Generate a terrain with many samples between the limits of the map
    xs = np.ogrid[0:5 * data["L"] + 4 * data["W"]:160j]
    ys = np.ogrid[0:data["P"] + data["W"] + data["D"]:160j]

    xSize = len(xs)
    ySize = len(ys)

    # Defining the location and colors of each vertex of the shape
    vertices = []
    indices = []

    # Generating a vertex for each sample x, y, and assigning a color
    for i in range(xSize):
        for j in range(ySize):
            x = xs[i]
            y = ys[j]

            vertices += [x, y, 0] + colorMap(x, y)

    # The previous loops generates full columns j-y and then move to
    # the next i-x. Hence, the index for each vertex i,j can be computed as
    index = lambda i, j: i * len(ys) + j 
    
    # We generate quads for each cell connecting 4 neighbor vertices
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):

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

    return bs.Shape(vertices, indices)


# Shape of the roof
def createRoof():

    # Defining the location and colors of each vertex of the shape
    vertices = []
    for vertex in keyPoints():
        vertices += vertex + [0.75, 0.75, 0.75] + [0, 0, -1]

    # Defining connections among vertices
    indices = [
           0,  5,  4,  0,  1,  5,  5,  1,  6,  6,  1,  7,
           7,  1,  8,  8,  1,  9,  9,  1, 10, 10,  1,  2,
          10, 11,  2, 11,  2, 12, 12,  2, 13, 13,  2,  3,
          13,  3, 33, 32, 23, 33, 32, 22, 23, 13, 33, 23,
          21, 11, 12, 21, 12, 31, 30, 21, 31, 30, 20, 21,
           9, 10, 19, 19, 10, 29, 28, 19, 29, 28, 18, 19,
           7,  8, 17, 17,  8, 27, 26, 17, 27, 26, 16, 17,
           5,  6, 15, 15,  6, 25, 24, 15, 25, 24, 14, 15]

    return bs.Shape(vertices, indices)


# Shape of the walls
def createWalls():

    # Defining the location and colors of each vertex of the shape
    vertices = []
    color = [0.75, 0.75, 0.75]

    # Points to use
    pts = keyPoints()
    hpts = list(map(lambda x: [x[0], x[1], 1], pts.copy()))

    # Drawing the walls
    vertices += pts[0] + color + [0, 1, 0] + hpts[0] + color + [0, 1, 0]
    vertices += pts[1] + color + [0, 1, 0] + hpts[1] + color + [0, 1, 0]
    vertices += pts[2] + color + [0, 1, 0] + hpts[2] + color + [0, 1, 0]
    vertices += pts[3] + color + [0, 1, 0] + hpts[3] + color + [0, 1, 0]
    vertices += pts[0] + color + [1, 0, 0] + hpts[0] + color + [1, 0, 0]
    vertices += pts[4] + color + [1, 0, 0] + hpts[4] + color + [1, 0, 0]
    vertices += pts[3] + color + [-1, 0, 0] + hpts[3] + color + [-1, 0, 0]
    vertices += pts[33] + color + [-1, 0, 0] + hpts[33] + color + [-1, 0, 0]
    vertices += pts[14] + color + [1, 0, 0] + hpts[14] + color + [1, 0, 0]
    vertices += pts[24] + color + [1, 0, 0] + hpts[24] + color + [1, 0, 0]
    vertices += pts[6] + color + [-1, 0, 0] + hpts[6] + color + [-1, 0, 0]
    vertices += pts[25] + color + [-1, 0, 0] + hpts[25] + color + [-1, 0, 0]
    vertices += pts[8] + color + [-1, 0, 0] + hpts[8] + color + [-1, 0, 0]
    vertices += pts[27] + color + [-1, 0, 0] + hpts[27] + color + [-1, 0, 0]
    vertices += pts[10] + color + [-1, 0, 0] + hpts[10] + color + [-1, 0, 0]
    vertices += pts[29] + color + [-1, 0, 0] + hpts[29] + color + [-1, 0, 0]
    vertices += pts[12] + color + [-1, 0, 0] + hpts[12] + color + [-1, 0, 0]
    vertices += pts[31] + color + [-1, 0, 0] + hpts[31] + color + [-1, 0, 0]
    vertices += pts[16] + color + [1, 0, 0] + hpts[16] + color + [1, 0, 0]
    vertices += pts[26] + color + [1, 0, 0] + hpts[26] + color + [1, 0, 0]
    vertices += pts[18] + color + [1, 0, 0] + hpts[18] + color + [1, 0, 0]
    vertices += pts[28] + color + [1, 0, 0] + hpts[28] + color + [1, 0, 0]
    vertices += pts[20] + color + [1, 0, 0] + hpts[20] + color + [1, 0, 0]
    vertices += pts[30] + color + [1, 0, 0] + hpts[30] + color + [1, 0, 0]
    vertices += pts[22] + color + [1, 0, 0] + hpts[22] + color + [1, 0, 0]
    vertices += pts[32] + color + [1, 0, 0] + hpts[32] + color + [1, 0, 0]
    vertices += pts[4] + color + [0, -1, 0] + hpts[4] + color + [0, -1, 0]
    vertices += pts[5] + color + [0, -1, 0] + hpts[5] + color + [0, -1, 0]
    vertices += pts[6] + color + [0, -1, 0] + hpts[6] + color + [0, -1, 0]
    vertices += pts[7] + color + [0, -1, 0] + hpts[7] + color + [0, -1, 0]
    vertices += pts[8] + color + [0, -1, 0] + hpts[8] + color + [0, -1, 0]
    vertices += pts[9] + color + [0, -1, 0] + hpts[9] + color + [0, -1, 0]
    vertices += pts[10] + color + [0, -1, 0] + hpts[10] + color + [0, -1, 0]
    vertices += pts[11] + color + [0, -1, 0] + hpts[11] + color + [0, -1, 0]
    vertices += pts[12] + color + [0, -1, 0] + hpts[12] + color + [0, -1, 0]
    vertices += pts[13] + color + [0, -1, 0] + hpts[13] + color + [0, -1, 0]
    vertices += pts[14] + color + [0, 1, 0] + hpts[14] + color + [0, 1, 0]
    vertices += pts[15] + color + [0, 1, 0] + hpts[15] + color + [0, 1, 0]
    vertices += pts[16] + color + [0, 1, 0] + hpts[16] + color + [0, 1, 0]
    vertices += pts[17] + color + [0, 1, 0] + hpts[17] + color + [0, 1, 0]
    vertices += pts[18] + color + [0, 1, 0] + hpts[18] + color + [0, 1, 0]
    vertices += pts[19] + color + [0, 1, 0] + hpts[19] + color + [0, 1, 0]
    vertices += pts[20] + color + [0, 1, 0] + hpts[20] + color + [0, 1, 0]
    vertices += pts[21] + color + [0, 1, 0] + hpts[21] + color + [0, 1, 0]
    vertices += pts[22] + color + [0, 1, 0] + hpts[22] + color + [0, 1, 0]
    vertices += pts[23] + color + [0, 1, 0] + hpts[23] + color + [0, 1, 0]
    vertices += pts[5] + color + [1, 0, 0] + hpts[5] + color + [1, 0, 0]
    vertices += pts[15] + color + [1, 0, 0] + hpts[15] + color + [1, 0, 0]
    vertices += pts[7] + color + [1, 0, 0] + hpts[7] + color + [1, 0, 0]
    vertices += pts[17] + color + [1, 0, 0] + hpts[17] + color + [1, 0, 0]
    vertices += pts[9] + color + [1, 0, 0] + hpts[9] + color + [1, 0, 0]
    vertices += pts[19] + color + [1, 0, 0] + hpts[19] + color + [1, 0, 0]
    vertices += pts[11] + color + [1, 0, 0] + hpts[11] + color + [1, 0, 0]
    vertices += pts[21] + color + [1, 0, 0] + hpts[21] + color + [1, 0, 0]
    vertices += pts[13] + color + [1, 0, 0] + hpts[13] + color + [1, 0, 0]
    vertices += pts[23] + color + [1, 0, 0] + hpts[23] + color + [1, 0, 0]

    # Drawing the heater
    vertices += pts[1] + [1, 0, 0] + [0, 1, 0] + hpts[1] + [1, 0, 0] + [0, 1, 0]
    vertices += pts[2] + [1, 0, 0] + [0, 1, 0] + hpts[2] + [1, 0, 0] + [0, 1, 0]

    # Drawing the bottom of the windows
    vertices += pts[24] + color + [0, -1, 0] + hpts[24][:2] + [0.3] + color + [0, -1, 0]
    vertices += pts[25] + color + [0, -1, 0] + hpts[25][:2] + [0.3]  + color + [0, -1, 0]
    vertices += pts[26] + color + [0, -1, 0] + hpts[26][:2] + [0.3] + color + [0, -1, 0]
    vertices += pts[27] + color + [0, -1, 0] + hpts[27][:2] + [0.3]  + color + [0, -1, 0]
    vertices += pts[28] + color + [0, -1, 0] + hpts[28][:2] + [0.3] + color + [0, -1, 0]
    vertices += pts[29] + color + [0, -1, 0] + hpts[29][:2] + [0.3]  + color + [0, -1, 0]
    vertices += pts[30] + color + [0, -1, 0] + hpts[30][:2] + [0.3] + color + [0, -1, 0]
    vertices += pts[31] + color + [0, -1, 0] + hpts[31][:2] + [0.3]  + color + [0, -1, 0]
    vertices += pts[32] + color + [0, -1, 0] + hpts[32][:2] + [0.3] + color + [0, -1, 0]
    vertices += pts[33] + color + [0, -1, 0] + hpts[33][:2] + [0.3]  + color + [0, -1, 0]

    # Defining connections among vertices
    indices = [
           0,  1,  2,  1,  3,  2,  4,  5,  6,  5,  7,  6,  8, 10,  9,
          10,  9, 11, 13, 14, 12, 13, 15, 14, 16, 18, 17, 17, 18, 19,
          21, 22, 20, 21, 23, 22, 25, 26, 24, 25, 27, 26, 29, 30, 28,
          29, 31, 30, 33, 34, 32, 33, 35, 34, 36, 38, 37, 37, 38, 39,
          40, 42, 41, 41, 42, 43, 44, 46, 45, 45, 46, 47, 48, 50, 49,
          49, 50, 51, 52, 54, 53, 53, 54, 55, 56, 58, 57, 57, 58, 59,
          60, 62, 61, 61, 62, 63, 64, 66, 65, 65, 66, 67, 68, 70, 69,
          69, 70, 71, 75, 74, 72, 75, 72, 73, 79, 78, 76, 79, 76, 77,
          83, 82, 80, 83, 80, 81, 87, 86, 84, 87, 84, 85, 91, 90, 88,
          91, 88, 89, 93, 92, 94, 93, 94, 95, 97, 96, 98, 97, 98, 99,
         101,100,102,101,102,103,105,104,106,105,106,107,109,108,110,
         109,110,111,112,113,114,113,115,114,117,116,118,117,118,119,
         121,120,122,121,122,123,125,124,126,125,126,127,129,128,130,
         129,130,131,133,132,134,133,134,135,
    ]
    return bs.Shape(vertices, indices)


# Moves the camera in a cylindrical system,
# returns the view matrix and the viewPos vector for later use
def moveCamera():

    theta = controller.cameraTheta

    # Where to look
    atX = controller.xPos + np.sin(theta)
    atY = controller.yPos + np.cos(theta)

    viewPos = np.array([controller.xPos, controller.yPos, 0.5])
    viewUp = np.array([0, 0, 1])

    return tr.lookAt(viewPos, np.array([atX, atY, 0.5]), viewUp), viewPos


# Main function
if __name__ == "__main__":

    # Initialize glfw
    if not glfw.init():
        sys.exit()

    width = 600
    height = 600

    window = glfw.create_window(width, height, "Heat map inside a Hotel.", None, None)

    if not window:
        glfw.terminate()
        sys.exit()

    glfw.make_context_current(window)

    # Connecting the callback function 'on_key' to handle keyboard events
    glfw.set_key_callback(window, on_key)

    # Defining shader programs
    #pipeline = ls.SimpleFlatShaderProgram()
    pipeline = ls.SimpleGouraudShaderProgram()
    #pipeline = ls.SimplePhongShaderProgram()
    simplePipeline = es.SimpleModelViewProjectionShaderProgram()

    glUseProgram(pipeline.shaderProgram)

    # Setting up the clear screen color
    glClearColor(0.85, 0.85, 0.85, 1.0)

    # As we work in 3D, we need to check which part is in front,
    # and which one is at the back
    glEnable(GL_DEPTH_TEST)

    # Creating the graphs
    roofGraph = sg.SceneGraphNode("roof")
    roofGraph.transform = tr.translate(0, 0, 1)
    roofGraph.childs += [es.toGPUShape(createRoof())]

    floorGraph = sg.SceneGraphNode("floor")
    floorGraph.childs += [es.toGPUShape(createFloor())]

    wallGraph = sg.SceneGraphNode("wall")
    wallGraph.childs += [es.toGPUShape(createWalls())]

    # Setting up the projection
    projection = tr.perspective(60, float(width) / float(height), 0.1, 100)

    # Light position
    lgX = 1.5 * data["L"] + data["W"]
    lgY = 1.5 * (data["P"] + data["W"] + data["D"])

    print("You can move with the arrow keys.")

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
        
        # The floow is drawn without light effects
        glUseProgram(simplePipeline.shaderProgram)
        glUniformMatrix4fv(glGetUniformLocation(simplePipeline.shaderProgram, "projection"), 1, GL_TRUE, projection)
        glUniformMatrix4fv(glGetUniformLocation(simplePipeline.shaderProgram, "view"), 1, GL_TRUE, view)
        glUniformMatrix4fv(glGetUniformLocation(simplePipeline.shaderProgram, "model"), 1, GL_TRUE, tr.identity())
        sg.drawSceneGraphNode(floorGraph, simplePipeline, "model")

        # Using the lighting shader program
        glUseProgram(pipeline.shaderProgram)
        glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "La"), 1.0, 1.0, 1.0)
        glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "Ld"), 1.0, 1.0, 1.0)
        glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "Ls"), 1.0, 1.0, 1.0)

        glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "Ka"), 0.2, 0.2, 0.2)
        glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "Kd"), 0.4, 0.4, 0.4)
        glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "Ks"), 0.4, 0.4, 0.4)

        glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "lightPosition"), lgX, lgY, 0.5)
        glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "viewPosition"), viewPos[0], viewPos[1], viewPos[2])
        glUniform1ui(glGetUniformLocation(pipeline.shaderProgram, "shininess"), 10)
        glUniform1f(glGetUniformLocation(pipeline.shaderProgram, "constantAttenuation"), 0.001)
        glUniform1f(glGetUniformLocation(pipeline.shaderProgram, "linearAttenuation"), 0.1)
        glUniform1f(glGetUniformLocation(pipeline.shaderProgram, "quadraticAttenuation"), 0.01)

        glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, "projection"), 1, GL_TRUE, projection)
        glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, "view"), 1, GL_TRUE, view)
        glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, "model"), 1, GL_TRUE, tr.identity())

        # Drawing the graphs
        sg.drawSceneGraphNode(wallGraph, pipeline, "model")
        sg.drawSceneGraphNode(roofGraph, pipeline, "model")

        # Once the drawing is rendered, buffers are swap so an uncomplete drawing is never seen.
        glfw.swap_buffers(window)

    glfw.terminate()