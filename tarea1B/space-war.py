import glfw
from OpenGL.GL import *
import OpenGL.GL.shaders
import numpy as np
import math
import random
import sys

# Local imports
import transformations as tr
import basic_shapes as bs
import scene_graph as sg
import easy_shaders as es


# Input from command line
N = sys.argv[1] if len(sys.argv) > 1 else "5"
N = int(N) if N.isdigit() else 5


# A class to store the application control
class Controller:
    fillPolygon = True
    fleet = 0
    enemies = []
    
    # Player data
    hp = 3
    score = 0
    xPos = 0.0
    yPos = 0.0
    readyToShot = False


# A class to store the data of an enemy
class Enemy:
    def __init__(self, name, ship):
        self.name = name
        self.ship = ship

    xPos = 0.0
    yPos = 0.0
    readyToShot = False


# Global controller that communicates with the callback function
controller = Controller()


def on_key(window, key, scancode, action, mods):

    global controller

    if key == glfw.KEY_A:
        controller.xPos = max(-0.8, controller.xPos - 0.05)

    elif key == glfw.KEY_S:
        controller.yPos = max(-1.0, controller.yPos - 0.1)

    elif key == glfw.KEY_D:
        controller.xPos = min(0.8, controller.xPos + 0.05)

    elif key == glfw.KEY_W:
        controller.yPos = min(1.0, controller.yPos + 0.1)

    elif action != glfw.PRESS:
        return
    
    elif key == glfw.KEY_F:
        print('Alternar relleno de figuras')
        controller.fillPolygon = not controller.fillPolygon

    elif key == glfw.KEY_SPACE:
        print('Disparo!')
        controller.readyToShot = True

    elif key == glfw.KEY_ESCAPE:
        sys.exit()

    else:
        print('Tecla desconocida')


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


# Creates a simple cannon, used by all spaceships
def createCannon():

    gpuGrayCube = es.toGPUShape(bs.createColorCube(0.8, 0.8, 0.8))
    gpuDarkCube = es.toGPUShape(bs.createColorCube(0.3, 0.3, 0.3))

    # A cannon is made of a tunnel section and a head
    tunnel = sg.SceneGraphNode("tunnel")
    tunnel.transform = tr.scale(0.1, 0.4, 1)
    tunnel.childs += [gpuGrayCube]

    head = sg.SceneGraphNode("head")
    head.transform = tr.matmul([tr.translate(0, -0.2, 0), tr.uniformScale(0.15)])
    head.childs += [gpuDarkCube]

    cannon = sg.SceneGraphNode("simpleCannon")
    cannon.childs += [tunnel]
    cannon.childs += [head]

    return cannon


# Creates a simple motor, used by all spaceships
def createMotor():

    gpuGrayTrapeze = es.toGPUShape(createColorTrapeze(0.6, 0.6, 0.6))

    gpuBlueTriangle = es.toGPUShape(createColorTriangle(0.2, 0.5, 1))
    gpuWhiteTriangle = es.toGPUShape(createColorTriangle(1, 1, 1))

    # A motor is made of a body and an animated flame
    blueFlame = sg.SceneGraphNode("blueFlame")
    blueFlame.transform = tr.matmul([tr.translate(0, 0.18, 1), tr.uniformScale(0.5)])
    blueFlame.childs += [gpuBlueTriangle]

    whiteFlame = sg.SceneGraphNode("whiteFlame")
    whiteFlame.transform = tr.matmul([tr.translate(0, 0.05, 1), tr.uniformScale(0.3)])
    whiteFlame.childs += [gpuWhiteTriangle]

    # This flame is animated in the main script
    animatedFlame = sg.SceneGraphNode("animatedFlame")
    animatedFlame.childs += [blueFlame]
    animatedFlame.childs += [whiteFlame]

    body = sg.SceneGraphNode("body")
    body.transform = tr.scale(1, 0.25, 1)
    body.childs += [gpuGrayTrapeze]

    # Joining both parts
    motor = sg.SceneGraphNode("simpleMotor")
    motor.childs += [animatedFlame]
    motor.childs += [body]

    return motor


# Creates an Avelyn ship, used by the player
def createAvelyn():

    gpuGrayTriangle = es.toGPUShape(createColorTriangle(0.4, 0.6, 0.4))

    gpuGrayTrapeze = es.toGPUShape(createColorTrapeze(0.6, 0.8, 0.6))
    gpuYellowTrapeze = es.toGPUShape(createColorTrapeze(1, 1, 0))

    gpuGrayCube0 = es.toGPUShape(bs.createColorCube(0.4, 0.6, 0.4))
    gpuGrayCube1 = es.toGPUShape(bs.createColorCube(0.6, 0.8, 0.6))
    gpuGrayCube2 = es.toGPUShape(bs.createColorCube(0.5, 0.7, 0.5))

    # Creating the cannon of the ship
    cannon = sg.SceneGraphNode("cannon")
    cannon.transform = tr.translate(0, -1.22, 1)
    cannon.childs += [createCannon()]

    # Creating the motor of the ship
    motor = sg.SceneGraphNode("motor")
    motor.transform = tr.translate(0, 0.95, 0)
    motor.childs += [createMotor()]

    # Creating the front of the ship
    front = sg.SceneGraphNode("front")
    front.transform = tr.matmul([tr.translate(0, -0.87, 0.5), tr.scale(0.6, -0.75, 1)])
    front.childs += [gpuGrayTriangle]

    # Creating the center of the ship
    center = sg.SceneGraphNode("center")
    center.transform = tr.scale(1, -1, 1)
    center.childs += [gpuGrayTrapeze]

    # Creating the cabin of the ship
    cabin = sg.SceneGraphNode("cabin")
    cabin.transform = tr.matmul([tr.translate(0, 0, 1), tr.uniformScale(-0.5)])
    cabin.childs += [gpuYellowTrapeze]

    # Creating extensions of the ship
    extension0 = sg.SceneGraphNode("extension0")
    extension0.transform = tr.matmul([tr.translate(0, 0.60, 0), tr.scale(1, 0.2, 1)])
    extension0.childs += [gpuGrayCube0]

    extension1 = sg.SceneGraphNode("extension1")
    extension1.transform = tr.matmul([tr.translate(0, 0.75, 0), tr.scale(1, 0.2, 1)])
    extension1.childs += [gpuGrayCube1]

    # Creating shapes to decorate the wings
    rectangle = sg.SceneGraphNode("rectangle")
    rectangle.transform = tr.scale(0.75, 1.5, 1)
    rectangle.childs += [gpuGrayCube2]

    decorated = sg.SceneGraphNode("decorated")
    decorated.transform = tr.matmul([tr.translate(0, 0.5, 0), tr.scale(0.8, 0.2, 1)])
    decorated.childs += [gpuGrayCube0]

    # Creating the wings of the ship
    wing0 = sg.SceneGraphNode("wing0")
    wing0.transform = tr.matmul([tr.translate(-0.6, 0.4, 0), tr.rotationZ(math.pi / 4)])
    wing0.childs += [rectangle]
    wing0.childs += [decorated]

    wing1 = sg.SceneGraphNode("wing1")
    wing1.transform = tr.scale(-1, 1, 1)
    wing1.childs += [wing0]

    # Joining all the parts
    avelyn = sg.SceneGraphNode("avelyn")
    avelyn.childs += [wing0, wing1]
    avelyn.childs += [motor, center, front]
    avelyn.childs += [extension0, extension1]
    avelyn.childs += [cabin]
    avelyn.childs += [cannon]

    return avelyn


# Creates an Woz ship, used by the enemies
# If "advanced", creates a green version with more cannons
def createWoz(advanced = False):

    # Variable used to change the colors
    # I preferred to use this over a different shader program
    # because I also need to use a different logic for the
    # advanced ships
    channel =  1- int(advanced)

    gpuVariantTriangle = es.toGPUShape(createColorTriangle(channel, 0.6, 0))

    gpuBlueTrapeze = es.toGPUShape(createColorTrapeze(0, 0, 1))
    gpuVariantTrapeze0 = es.toGPUShape(createColorTrapeze(channel, 1 - channel, 0))
    gpuVariantTrapeze1 = es.toGPUShape(createColorTrapeze(channel, 0.4, 0))
    
    # Creating the cannon of the ship
    cannon = sg.SceneGraphNode("cannon")
    cannon.transform = tr.translate(0, -1.22, 1)
    cannon.childs += [createCannon()]

    # Creating the motor of the ship
    motor = sg.SceneGraphNode("motor")
    motor.transform = tr.translate(0, 0.62, 0)
    motor.childs += [createMotor()]

    # Creating the front of the ship
    front = sg.SceneGraphNode("front")
    front.transform = tr.matmul([tr.translate(0, -0.87, 0.5), tr.scale(0.6, -0.75, 1)])
    front.childs += [gpuVariantTriangle]

    # Creating the center of the ship
    center = sg.SceneGraphNode("center")
    center.transform = tr.scale(1, -1, 1)
    center.childs += [gpuVariantTrapeze0]

    # Creating the cabin of the ship
    cabin = sg.SceneGraphNode("cabin")
    cabin.transform = tr.matmul([tr.translate(0, 0, 1), tr.uniformScale(-0.5)])
    cabin.childs += [gpuBlueTrapeze]

    # Creating the wings of the ship
    wing0 = sg.SceneGraphNode("wing0")
    wing0.transform = tr.matmul([tr.uniformScale(0.5), tr.rotationZ(math.pi / 2)])
    wing0.transform = tr.matmul([tr.shearing(0, 1.2, 0, 0, 0, 0), wing0.transform])
    wing0.transform = tr.matmul([tr.translate(-0.6, -0.25, 0), tr.rotationZ(0.2), wing0.transform])
    wing0.childs += [gpuVariantTrapeze1]

    wing1 = sg.SceneGraphNode("wing1")
    wing1.transform = tr.matmul([tr.scale(-1, 1, 1), wing0.transform])
    wing1.childs += [gpuVariantTrapeze1]

    woz = sg.SceneGraphNode("woz")
    woz.childs += [wing0, wing1]
    woz.childs += [motor, center, front]
    woz.childs += [cabin]
    woz.childs += [cannon]

    # Upgrading the Woz
    if advanced:
        extraCannon0 = sg.SceneGraphNode("extraCannon0")
        extraCannon0.transform = tr.matmul([tr.translate(0.75, 0.5, 0), cannon.transform])
        extraCannon0.childs += [createCannon()]

        extraCannon1 = sg.SceneGraphNode("extraCannon1")
        extraCannon1.transform = tr.matmul([tr.scale(-1, 1, 1), extraCannon0.transform])
        extraCannon1.childs += [createCannon()]

        woz.childs += [extraCannon0, extraCannon1]

    return woz


def createEnemies(N):

    global controller

    for i in range(N):
        # A new node is only locating a enemyShip in the scene depending on index i
        enemy = createEnemy((i + 1) % 5 == 0)
        enemy.name += str(i)
        enemy.ship.transform = tr.translate(1 / (N - 1) * i - 0.5, 0, 0)

        # Now this ship is added to the global list of enemies
        controller.enemies += [enemy]


# Creates the ship used by the player, its properties are
# affected by the global controller.
def createPlayer():

    ship = createAvelyn()

    # Moving the ship to the bottom of the screen and making it small
    traslatedShip = sg.SceneGraphNode("traslatedShip")
    traslatedShip.transform = tr.matmul([tr.translate(0, -0.8, 0), tr.uniformScale(-0.1)])
    traslatedShip.childs += [ship]

    player = sg.SceneGraphNode("player")
    player.childs += [traslatedShip]

    return player


# Creates an enemy
# If "advanced", creates a stronger enemy
def createEnemy(advanced = False):

    global controller

    random.seed()

    ship = createWoz(advanced)

    # Moving the ship to the top of the screen and making it small
    traslatedShip = sg.SceneGraphNode("traslatedShip")
    traslatedShip.transform = tr.matmul([tr.translate(0, 0.8, 0), tr.uniformScale(0.1)])
    traslatedShip.childs += [ship]

    # Giving a specific name to advanced enemies in order to apply
    # different logic
    name = "advanced" if advanced else "enemy"
    enemyShip = sg.SceneGraphNode(name)
    enemyShip.childs += [traslatedShip]

    enemy = Enemy(name, enemyShip)

    # Puts the enemy in an empty area
    xSpawn = 0.0
    sign = random.randrange(-1, 2, 2)

    for friend in controller.enemies:
        xPos = friend.xPos

        if xPos + 0.1 >= xSpawn >= xPos - 0.1:
            xSpawn += 0.2 * sign
    
    enemy.xPos = xSpawn

    return enemy


# Draws the enemies on screen and animates its flames
def drawEnemies(pipeline, time):

    global controller

    for enemy in controller.enemies:

        ship = enemy.ship

        ship.transform = tr.translate(enemy.xPos, enemy.yPos, 0)
        sg.drawSceneGraphNode(ship, pipeline, "transform")
    
        animatedFlame = sg.findNode(ship, "animatedFlame")
        animatedFlame.transform = tr.translate(0, 0.2 * np.sin(1.2 * time), 0)


# Main function
if __name__ == "__main__":

    # Initialize glfw
    if not glfw.init():
        sys.exit()

    width = 600
    height = 600

    window = glfw.create_window(width, height, "SPACE WAR", None, None)

    if not window:
        glfw.terminate()
        sys.exit()

    glfw.make_context_current(window)

    # Connecting the callback function 'on_key' to handle keyboard events
    glfw.set_key_callback(window, on_key)

    # Assembling the shader program (pipeline) with both shaders
    pipeline = es.SimpleTransformShaderProgram()
    
    # Telling OpenGL to use our shader program
    glUseProgram(pipeline.shaderProgram)

    # Setting up the clear screen color
    glClearColor(0.0, 0.0, 0.0, 1.0)

    # Creating shapes on GPU memory
    createEnemies(5)
    player = createPlayer()

    while not glfw.window_should_close(window):
        # Using GLFW to check for input events
        glfw.poll_events()

        # Filling or not the shapes depending on the controller state
        if (controller.fillPolygon):
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

        # Clearing the screen in both, color and depth
        glClear(GL_COLOR_BUFFER_BIT)

        time = 10 * glfw.get_time()

        flameNode = sg.findNode(player, "animatedFlame")
        flameNode.transform = tr.translate(0, 0.2 * np.sin(1.2 * time), 0)

        # Drawing the enemies
        drawEnemies(pipeline, time)

        # Drawing the Player
        player.transform = tr.translate(controller.xPos, 0, 0)
        sg.drawSceneGraphNode(player, pipeline, "transform")

        animatedFlame = sg.findNode(player, "animatedFlame")
        animatedFlame.transform = tr.translate(0, 0.2 * np.sin(1.2 * time), 0)

        # Once the render is done, buffers are swapped, showing only the complete scene.
        glfw.swap_buffers(window)

    glfw.terminate()