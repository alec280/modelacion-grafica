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


# Class that stores the application control
class Controller:
    def __init__(self):
        self.fillPolygon = True


# Global controller that communicates with the callback function
controller = Controller()


def on_key(window, key, scancode, action, mods):

    if action != glfw.PRESS:
        return
    
    global controller

    if key == glfw.KEY_SPACE:
        controller.fillPolygon = not controller.fillPolygon

    elif key == glfw.KEY_ESCAPE:
        sys.exit()


# Colorates the heat map with 3 colors.
def colorMap(value, active):
    if not active:
        return [0, 0, 0]


# Shape of the floor and roof
def blueprint(floor = False):
    global data

    normal = [0, 0, 1] if floor else [0, 0, -1]
    
    # Geometry of the problem
    P = data["P"]
    L = data["L"]
    D = data["D"]
    W = data["W"]
    E = data["E"]
    H1 = data["H1"]
    H2 = data["H2"]

    # Defining the location and colors of each vertex  of the shape
    vertices = []
    for vertex in [
        [0, 0, 0], #0
        [H1, 0, 0],
        [H2, 0, 0], 
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
        [5 * L + 4 * W, P + W + D, 0]
    ]:
        vertices += vertex + colorMap(vertex, floor) + normal 

    # Defining connections among vertices
    indices = [
           0,  5,  4, 
           0,  1,  5,
           5,  1,  6,
           6,  1,  7,
           7,  1,  8,
           8,  1,  9,
           9,  1, 10,
          10,  1,  2,
          10, 11,  2,
          11,  2, 12,
          12,  2, 13,
          13,  2,  3,
          13,  3, 33,
          32, 23, 33,
          32, 22, 23,
          13, 33, 23,
          21, 11, 12,
          21, 12, 31,
          30, 21, 31,
          30, 20, 21,
           9, 10, 19,
          19, 10, 29,
          28, 19, 29,
          28, 18, 19,
           7,  8, 17,
          17,  8, 27,
          26, 17, 27,
          26, 16, 17,
           5,  6, 15,
          15,  6, 25,
          24, 15, 25,
          24, 14, 15,
    ]
    return bs.Shape(vertices, indices)


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

    # Telling OpenGL to use our shader program
    glUseProgram(pipeline.shaderProgram)

    # Setting up the clear screen color
    glClearColor(0.85, 0.85, 0.85, 1.0)

    # As we work in 3D, we need to check which part is in front,
    # and which one is at the back
    glEnable(GL_DEPTH_TEST)

    # Creating shapes on GPU memory
    gpuRoof = es.toGPUShape(blueprint())

    t0 = glfw.get_time()
    camera_theta = -3*np.pi/4

    while not glfw.window_should_close(window):
        # Using GLFW to check for input events
        glfw.poll_events()

        # Getting the time difference from the previous iteration
        t1 = glfw.get_time()
        dt = t1 - t0
        t0 = t1

        if (glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS):
            camera_theta -= 2 * dt

        if (glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS):
            camera_theta += 2* dt

        # Setting up the view transform
        R = 12
        camX = R * np.sin(camera_theta)
        camY = R * np.cos(camera_theta)
        viewPos = np.array([camX, camY, 7])
        view = tr.lookAt(
            viewPos,
            np.array([0,0,1]),
            np.array([0,0,1])
        )

        # Setting up the projection transform
        projection = tr.perspective(60, float(width)/float(height), 0.1, 100)

        # Clearing the screen in both, color and depth
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Filling or not the shapes depending on the controller state
        if (controller.fillPolygon):
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

        # Drawing shapes
        glUseProgram(pipeline.shaderProgram)
        glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "La"), 1.0, 1.0, 1.0)
        glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "Ld"), 1.0, 1.0, 1.0)
        glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "Ls"), 1.0, 1.0, 1.0)

        glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "Ka"), 0.2, 0.2, 0.2)
        glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "Kd"), 0.9, 0.9, 0.9)
        glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "Ks"), 1.0, 1.0, 1.0)

        glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "lightPosition"), -3, 0, 3)
        glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "viewPosition"), viewPos[0], viewPos[1], viewPos[2])
        glUniform1ui(glGetUniformLocation(pipeline.shaderProgram, "shininess"), 100)
        glUniform1f(glGetUniformLocation(pipeline.shaderProgram, "constantAttenuation"), 0.001)
        glUniform1f(glGetUniformLocation(pipeline.shaderProgram, "linearAttenuation"), 0.1)
        glUniform1f(glGetUniformLocation(pipeline.shaderProgram, "quadraticAttenuation"), 0.01)

        glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, "projection"), 1, GL_TRUE, projection)
        glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, "view"), 1, GL_TRUE, view)
        glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, "model"), 1, GL_TRUE, tr.identity())

        pipeline.drawShape(gpuRoof)

        # Once the drawing is rendered, buffers are swap so an uncomplete drawing is never seen.
        glfw.swap_buffers(window)

    glfw.terminate()