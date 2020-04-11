"""
Alexander Cuevas, CC3501, 2020-1
Creates visuals that don't affect
the gameplay, like explosions, the
background and a basic HUD.
"""

from PIL import Image
from OpenGL.GL import GL_CLAMP_TO_EDGE, GL_LINEAR
import glfw
import math
import numpy as np

# Local imports
import transformations as tr
import basic_shapes as bs
import scene_graph as sg
import easy_shaders as es


# Creates a basic triangle of any color
def createColorTriangle(r, g, b):

    vertices = [
    #   positions         colors
        -0.5, -0.5, 0.0,  r, g, b,
         0.5, -0.5, 0.0,  r, g, b,
         0.0,  0.5, 0.0,  r, g, b]

    # Connections among vertices
    indices = [0, 1, 2]

    return bs.Shape(vertices, indices)


# Creates a basic trapeze of any color
def createColorTrapeze(r, g, b):

    vertices = [
    #   positions         colors
        -0.5, -0.5, 0.0,  r, g, b,
         0.5, -0.5, 0.0,  r, g, b,
        -0.3,  0.5, 0.0,  r, g, b,
         0.3,  0.5, 0.0,  r, g, b]

    # Connections among vertices
    indices = [0, 1, 3, 3, 2, 0]

    return bs.Shape(vertices, indices)


# Creates a white-orange explosion, used when a ship is destroyed
def createExplosion():
    
    gpuWhiteTriangle = es.toGPUShape(createColorTriangle(1, 1, 1))
    gpuOrangeTriangle = es.toGPUShape(createColorTriangle(1, 0.5, 0))

    whitePart = sg.SceneGraphNode("whitePart")
    whitePart.transform = tr.uniformScale(0.7)

    orangePart = sg.SceneGraphNode("orangePart")

    theta = math.pi

    # Creating the white part
    tri0 = sg.SceneGraphNode("tri0")
    tri0.transform = tr.matmul([tr.translate(0, -0.15, 0), tr.rotationZ(theta)])
    tri0.childs += [gpuWhiteTriangle]

    tri1 = sg.SceneGraphNode("tri1")
    tri1.transform = tr.matmul([tr.translate(0, 0.15, 0), tr.rotationZ(theta * 2)])
    tri1.childs += [gpuWhiteTriangle]

    whitePart.childs += [tri0, tri1]

    # Creating the orange part
    angle0 = sg.SceneGraphNode("angle0")
    angle0.transform = tr.matmul([tr.translate(0, -0.15, 0), tr.rotationZ(theta)])
    angle0.childs += [gpuOrangeTriangle]

    angle1 = sg.SceneGraphNode("angle1")
    angle1.transform = tr.matmul([tr.translate(0, 0.15, 0), tr.rotationZ(theta * 2)])
    angle1.childs += [gpuOrangeTriangle]

    orangePart.childs += [angle0, angle1]
    
    # Joining both parts
    explosion = sg.SceneGraphNode("explosion")
    explosion.childs = [orangePart, whitePart]

    return explosion


# Creates a background composed of 3 layers
# Animated in the main script through the controller
def createBackground():
    
    gpuFarQuad = es.toGPUShape(bs.createColorQuad(0.1, 0.1, 0.1))
    gpuMediumQuad = es.toGPUShape(bs.createColorQuad(0.2, 0.2, 0.2))
    gpuCloseQuad = es.toGPUShape(bs.createColorQuad(0.3, 0.3, 0.3))

    # Creating the shape of the stars
    farQuad = sg.SceneGraphNode("farQuad")
    farQuad.transform = tr.matmul([tr.rotationZ(math.pi / 4), tr.uniformScale(0.04)])
    farQuad.transform = tr.matmul([tr.scale(0.8, 1, 0), farQuad.transform])
    farQuad.childs += [gpuFarQuad]

    mediumQuad = sg.SceneGraphNode("mediumQuad")
    mediumQuad.transform = farQuad.transform
    mediumQuad.childs += [gpuMediumQuad]

    closeQuad = sg.SceneGraphNode("closeQuad")
    closeQuad.transform = farQuad.transform
    closeQuad.childs += [gpuCloseQuad]

    farLayer = sg.SceneGraphNode("farLayer")
    mediumLayer = sg.SceneGraphNode("mediumLayer")
    closeLayer = sg.SceneGraphNode("closeLayer")

    # Adding the stars at random
    sequence = np.random.randint(-9, 10, (3, 12, 2))

    for dup in sequence[0]:
        farStar = sg.SceneGraphNode("farQuad")
        farStar.transform = tr.translate(dup[0] / 10.0, dup[1] / 10.0, 0)
        farStar.childs += [farQuad]

        farLayer.childs += [farStar]
    
    for dup in sequence[1]:
        mediumStar = sg.SceneGraphNode("mediumQuad")
        mediumStar.transform = tr.translate(dup[0] / 10.0, dup[1] / 10.0, 0)
        mediumStar.childs += [mediumQuad]

        mediumLayer.childs += [mediumStar]
    
    for dup in sequence[2]:
        closeStar = sg.SceneGraphNode("closeQuad")
        closeStar.transform = tr.translate(dup[0] / 10.0, dup[1] / 10.0, 0)
        closeStar.childs += [closeQuad]

        closeLayer.childs += [closeStar]
    
    # Joining the layers
    background = sg.SceneGraphNode("background")
    background.transform = tr.translate(0, 1, 0)
    background.childs += [farLayer]
    background.childs += [mediumLayer]
    background.childs += [closeLayer]

    # An extension of the background in order to allow
    # limited scrolling
    backgroundExtra = sg.SceneGraphNode("backgroundExtra")
    backgroundExtra.transform = tr.translate(0, -2, 0)
    backgroundExtra.childs += [background]

    finalBackground = sg.SceneGraphNode("finalBackground")
    finalBackground.childs = [background, backgroundExtra]

    return finalBackground


# Creates a green or red bar used to show the hp
# of the player
def createLifeBar(green = True):

    channel = int(green)

    vertices = [
    #   positions         colors
        -0.5, -0.5, 0.0,  1 - channel, channel, 0,
         0.5, -0.5, 0.0,  1 - channel, channel, 0,
         0.5,  0.5, 0.0,            1,       1, 1,
        -0.5,  0.5, 0.0,  1 - channel, channel, 0]

    # Defining connections among vertices
    indices = [0, 1, 2, 2, 3, 0]

    gpuShape = es.toGPUShape(bs.Shape(vertices, indices))

    # Creating an elongated bar
    scaledBar = sg.SceneGraphNode("scaledBar")
    scaledBar.transform = tr.scale(0.1, 0.03, 1)
    scaledBar.childs += [gpuShape]

    bar = sg.SceneGraphNode("bar")
    bar.childs += [scaledBar]

    return bar


# Creates a texture with the text "GAME OVER"
# or "VICTORY" that covers all the screen
def createGameOver(victory = False):

    image = "victory_texture.png" if victory else "game_over_texture.png"
    textureShape = es.toGPUShape(bs.createTextureQuad(image), GL_CLAMP_TO_EDGE, GL_LINEAR)

    texture = sg.SceneGraphNode("texture")
    texture.transform = tr.uniformScale(2)
    texture.childs += [textureShape]

    return texture
