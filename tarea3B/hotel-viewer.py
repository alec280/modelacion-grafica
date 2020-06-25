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

# Import that helps to get the contours
import matplotlib.pyplot as mpl


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
        print('\n' + "Loading solution...", end = ' ')
except:
    print('\n' + "Solution not found.")
    sys.exit()

solution = np.load(solution_name)
shapeSol = solution.shape

# Precision of the solution
PRECISION = 0.1

# Checks minimal and maximal values for the heat map
minval = np.min(solution[np.nonzero(solution)])
maxval = np.max(solution)
midval = (maxval + minval) / 2


# Class that stores the application control
class Controller:
    def __init__(self):
        self.cameraPhi = np.pi / 2
        self.cameraTheta = np.pi / 4
        self.xPos = data["L"] / 2
        self.yPos = data["P"] / 2
        self.curves = False
        self.arrows = False


# Global controller that communicates with the callback function
controller = Controller()


# Helps to control the camera by snapping it to these degrees
SNAP_ANGLES = np.array([0, np.pi / 4, np.pi / 2, 3 * np.pi / 4, np.pi, 
                        5 * np.pi / 4, 3 * np.pi / 2, 7 * np.pi / 4, 2 * np.pi])


# Handles the interaction with the user
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
        
        if abs(controller.cameraPhi - np.pi / 2) < 0.1:
            controller.cameraPhi = np.pi / 2

        controller.xPos += 0.1 * sign * np.cos(controller.cameraTheta)
        controller.yPos += 0.1 * sign * np.sin(controller.cameraTheta)

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
        controller.cameraTheta = (controller.cameraTheta - np.pi / 90) % (2 * np.pi)
    
    elif key == glfw.KEY_LEFT:
        controller.cameraTheta = (controller.cameraTheta + np.pi / 90) % (2 * np.pi)
    
    elif key == glfw.KEY_W:
        angle = controller.cameraPhi - np.pi / 90
        controller.cameraPhi = angle if angle >= np.pi / 3 else np.pi / 3
    
    elif key == glfw.KEY_S:
        angle = controller.cameraPhi + np.pi / 90
        controller.cameraPhi = angle if angle <= 3 * np.pi / 4 else 3 * np.pi / 4

    elif action != glfw.PRESS:
        return
    
    elif key == glfw.KEY_SPACE:
        controller.curves = not controller.curves
    
    elif key == glfw.KEY_RIGHT_CONTROL:
        controller.arrows = not controller.arrows

    elif key == glfw.KEY_ESCAPE:
        sys.exit()


# Colorates the heat map with 3 colors
def colorMap(i, j):

    # Getting the temperature
    x = min(int(i / PRECISION + 0.0001), shapeSol[0] - 1)
    y = min(int(j / PRECISION + 0.0001), shapeSol[1] - 1)

    return colorAux(solution[x, y])


# Returns the appropiate color for a temperature
def colorAux(temperature):
    colorMin = np.array([0, 0, 1])
    colorMid = np.array([1, 1, 1])
    colorMax = np.array([1, 0, 0])

    # Assigning the colors
    if temperature <= minval:
        return list(colorMin)
    elif minval < temperature < midval:
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
    xs = np.ogrid[0:5 * data["L"] + 4 * data["W"]:np.complex(shapeSol[0], 1)]
    ys = np.ogrid[0:data["P"] + data["W"] + data["D"]:np.complex(shapeSol[1], 1)]

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
                ine, inw, isw]

    return bs.Shape(vertices, indices)


# Shape of the roof
def createRoof():

    # Defining the location and colors of each vertex of the shape
    vertices = []

    pts = keyPoints()
    for vertex in [pts[0], pts[3], pts[24], pts[33]]:
        vertices += vertex + [0.75, 0.75, 0.75] + [0, 0, -1]

    # Defining connections among vertices
    indices = [2, 0, 1, 2, 1, 3]

    return bs.Shape(vertices, indices)


# Shape of a curve
def createCurve(curve, level):

    z = (level - minval) / (maxval - minval)
    color = list((np.array(colorAux(level)) + np.array([1, 1, 1])) * 0.5)

    # Defining the location and colors of each vertex of the shape
    vertices = []

    # This shape is meant to be drawn with GL_LINES
    indices = []

    for i, pos in enumerate(curve):
        vertices += [pos[0] * PRECISION, pos[1] * PRECISION, z] + color
        indices += [i, i + 1]

    indices.pop()

    return bs.Shape(vertices, indices)


# Calculate the gradient of a point
def calculateGradient(i, j):

    zUp = solution[i - 1, j] if i > 0 else solution[i, j]
    zDown = solution[i + 1, j] if i < shapeSol[0] - 1 else solution[i, j]
    zLeft = solution[i, j - 1] if j > 0 else solution[i, j]
    zRight = solution[i, j + 1] if j < shapeSol[1] - 1 else solution[i, j]

    # Calculating the derivatives by approximation
    x = (zDown - zUp) / (2 * PRECISION)
    y = (zRight - zLeft) / (2 * PRECISION)

    # Returns the vertex value (normalized) and its magnitude
    vertex = np.array([x, y, 0.0])
    normalized = vertex / np.linalg.norm(vertex)

    magnitude = min(1, np.sqrt(x**2 + y**2))

    return (normalized, magnitude)


# Shape of the arrow map
def createArrowMap():

    # Defining the location and colors of each vertex of the shape
    vertices = []

    # This shape is meant to be drawn with GL_LINES
    indices = []

    for i in range(shapeSol[0]):
        for j in range(shapeSol[1]):
            k = j + i * shapeSol[0]

            color = [0, 0, 0]

            # Getting the gradient
            gradient, magnitude = calculateGradient(i, j)
            vertex = np.array([i * PRECISION, j * PRECISION, 0.05])
            end_point = vertex + 0.07 * magnitude * gradient

            middle = (vertex + end_point) / 2

            # Creating the arrowhead
            perpendicular = np.cross(end_point - vertex, [0, 0, 1])
            perpendicular /= np.linalg.norm(perpendicular)

            # Adding the arrow
            vertices += list(vertex) + color + list(end_point) + color
            vertices += list(middle + 0.02 * magnitude * perpendicular) + color
            vertices += list(middle - 0.02 * magnitude * perpendicular) + color

            indices += [4 * k, 4 * k + 1, 4 * k + 1, 4 * k + 2, 4 * k + 1, 4 * k + 3]

    return bs.Shape(vertices, indices)


# Shape of the walls
def createWalls():
    global data

    # Defining the location and colors of each vertex of the shape
    vertices = []
    color = [0.75, 0.75, 0.75]

    # Points to use
    pts = keyPoints()
    hpts = list(map(lambda x: [x[0], x[1], 1], pts.copy()))

    # Drawing the walls
    # Drawing the bottom walls
    for i in range(0, 4):
        vertices += pts[i] + color + [0, 1, 0] + hpts[i] + color + [0, 1, 0]

    # Unorganized group of walls
    vertices += pts[0] + color + [1, 0, 0] + hpts[0] + color + [1, 0, 0]
    vertices += pts[4] + color + [1, 0, 0] + hpts[4] + color + [1, 0, 0]
    vertices += pts[3] + color + [-1, 0, 0] + hpts[3] + color + [-1, 0, 0]
    vertices += pts[33] + color + [-1, 0, 0] + hpts[33] + color + [-1, 0, 0]
    vertices += pts[14] + color + [1, 0, 0] + hpts[14] + color + [1, 0, 0]
    vertices += pts[24] + color + [1, 0, 0] + hpts[24] + color + [1, 0, 0]

    # Drawing the walls perpendicual to the heater (big)
    for i in range(6, 14, 2):
        vertices += pts[i] + color + [-1, 0, 0] + hpts[i] + color + [-1, 0, 0]
        vertices += pts[i + 19] + color + [-1, 0, 0] + hpts[i + 19] + color + [-1, 0, 0]

    for i in range(16, 24, 2):
        vertices += pts[i] + color + [1, 0, 0] + hpts[i] + color + [1, 0, 0]
        vertices += pts[i + 10] + color + [1, 0, 0] + hpts[i + 10] + color + [1, 0, 0]

    # Drawing the walls parallel to the heater
    for i in range(4, 14):
        vertices += pts[i] + color + [0, -1, 0] + hpts[i] + color + [0, -1, 0]
    
    for i in range(14, 24):
        vertices += pts[i] + color + [0, 1, 0] + hpts[i] + color + [0, 1, 0]

    # Drawing the walls perpendicual to the heater (small)
    for i in range(5, 15, 2):
        vertices += pts[i] + color + [1, 0, 0] + hpts[i] + color + [1, 0, 0]
        vertices += pts[i + 10] + color + [1, 0, 0] + hpts[i + 10] + color + [1, 0, 0]

    # Drawing the heater
    for i in range(1, 3):
        vertices += pts[i] + [1, 0, 0] + [0, 1, 0] + hpts[i] + [1, 0, 0] + [0, 1, 0]

    # Drawing the bottom of the windows
    for i in range(24, 34):
        vertices += pts[i] + color + [0, -1, 0] + hpts[i][:2] + [0.3] + color + [0, -1, 0]

    # Drawing the open or closed windows
    windows = data["windows"]
    glass_colors = [[0.5, 0.5, 1], [1, 1, 0]]

    for i, j in enumerate(range(24, 34)):
        glass = glass_colors[windows[i // 2]]
        vertices += pts[j][:2] + [0.3] + glass + [0, 1, 0] + hpts[j] + glass + [0, 1, 0]

    # Defining connections among vertices
    indices = []

    for i in range(0, 156, 4):
        indices += [i + 1, i, i + 2, i + 1, i + 2, i + 3]

    return bs.Shape(vertices, indices)


# Moves the camera in a spherical system,
# returns the view matrix and the viewPos vector for later use
def moveCamera():

    phi = controller.cameraPhi
    theta = controller.cameraTheta

    # Where to look
    atX = controller.xPos + np.cos(theta) * np.sin(phi)
    atY = controller.yPos + np.sin(theta) * np.sin(phi)
    atZ = 0.5 + np.cos(phi)

    viewPos = np.array([controller.xPos, controller.yPos, 0.5])
    viewUp = np.array([0, 0, 1])

    return tr.lookAt(viewPos, np.array([atX, atY, atZ]), viewUp), viewPos


# Get the contours from matplotlib
def get_contour_verts(cn):
    contours = []

    # For each contour line
    for cc in cn.collections:
        paths = []

        # For each separate section of the contour line
        for pp in cc.get_paths():
            xy = []
            # for each segment of that section
            for vv in pp.iter_segments():
                xy.append(vv[0])
            paths.append(np.vstack(xy))
        contours.append(paths)

    return contours


# Main function
if __name__ == "__main__":

    # Initialize glfw
    if not glfw.init():
        sys.exit()

    width = 600
    height = 600

    window = glfw.create_window(width, height, "Heat map inside Don Pedro's hotel.", None, None)

    if not window:
        glfw.terminate()
        sys.exit()

    glfw.make_context_current(window)

    # Connecting the callback function 'on_key' to handle keyboard events
    glfw.set_key_callback(window, on_key)

    # Defining shader programs
    #pipeline = ls.SimpleFlatShaderProgram()
    #pipeline = ls.SimpleGouraudShaderProgram()
    pipeline = ls.SimplePhongShaderProgram()
    simplePipeline = es.SimpleModelViewProjectionShaderProgram()

    glUseProgram(pipeline.shaderProgram)

    # Setting up the clear screen color
    glClearColor(0.85, 0.85, 0.85, 1.0)

    # As we work in 3D, we need to check which part is in front,
    # and which one is at the back
    glEnable(GL_DEPTH_TEST)

    # Filling the shapes
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    # Getting the contours
    x, y = np.mgrid[:shapeSol[0], :shapeSol[1]]
    cnt = mpl.contour(x, y, solution, 12)

    cnt_list = get_contour_verts(cnt)[1:11]
    cnt_levels = cnt.levels[1:11]

    # Creating the graphs
    roofGraph = sg.SceneGraphNode("roof")
    roofGraph.transform = tr.translate(0, 0, 1)
    roofGraph.childs += [es.toGPUShape(createRoof())]

    floorGraph = sg.SceneGraphNode("floor")
    floorGraph.childs += [es.toGPUShape(createFloor())]

    wallGraph = sg.SceneGraphNode("wall")
    wallGraph.childs += [es.toGPUShape(createWalls())]

    curvesGpu = []
    for contour, level in zip(cnt_list, cnt_levels):
        curvesGpu.append(es.toGPUShape(createCurve(contour[0], level)))
    
    arrowGpu = es.toGPUShape(createArrowMap())

    # Setting up the projection
    projection = tr.perspective(60, float(width) / float(height), 0.1, 100)

    # Light position
    lgX = 2.5 * data["L"] + 2 * data["W"]
    lgY = 2 * (data["P"] + data["W"] + data["D"])

    print("Solution loaded." + '\n')
    print("Minimum value (Blue):", "{:.2f}".format(minval))
    print("Intermediate value (White):", "{:.2f}".format(midval))
    print("Maximum value (Red):", "{:.2f}".format(maxval), '\n')
    print("You can move with the arrow keys and tilt the view with the W and S keys" + '\n')

    while not glfw.window_should_close(window):
        # Using GLFW to check for input events
        glfw.poll_events()

        # Moving the camera
        view, viewPos = moveCamera()

        # Clearing the screen in both, color and depth
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # The floor and curves are drawn without light effects
        glUseProgram(simplePipeline.shaderProgram)
        glUniformMatrix4fv(glGetUniformLocation(simplePipeline.shaderProgram, "projection"), 1, GL_TRUE, projection)
        glUniformMatrix4fv(glGetUniformLocation(simplePipeline.shaderProgram, "view"), 1, GL_TRUE, view)
        glUniformMatrix4fv(glGetUniformLocation(simplePipeline.shaderProgram, "model"), 1, GL_TRUE, tr.identity())
        sg.drawSceneGraphNode(floorGraph, simplePipeline, "model")

        # Drawing the curves
        if controller.curves:
            for curve in curvesGpu:
                simplePipeline.drawShape(curve, GL_LINES)
        
        # Drawing the arrows
        if controller.arrows:
            simplePipeline.drawShape(arrowGpu, GL_LINES)

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