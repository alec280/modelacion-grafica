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

# Local imports (created by me)
import ship_factory as sf


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


# Creates the ship used by the player, its properties are
# affected by the global controller.
def createPlayer():

    # Ship created in ship factory
    ship = sf.createAvelyn()

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

    # Ship created in ship factory
    ship = sf.createWoz(advanced)

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


# Creates "n" enemies, each 5 enemies are advanced
def createEnemies(n):

    global controller

    if controller.fleet == N or len(controller.enemies) == 4:
        return

    for _ in range(n):
        # Creates a new enemy with a unique name
        controller.fleet += 1
        i = controller.fleet
        enemies = controller.enemies

        enemy = createEnemy(i % 5 == 0)
        enemy.name += str(i - 1)
        enemies.append(enemy)

        # There can only be 4 enemies on screen
        if len(enemies) == 4 or i == N:
            break


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
    createEnemies(4)
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

        # Creating and drawing the enemies
        if int(time) % 5 == 0:
            createEnemies(1)
        drawEnemies(pipeline, time)

        # Drawing the Player
        player.transform = tr.translate(controller.xPos, 0, 0)
        sg.drawSceneGraphNode(player, pipeline, "transform")

        animatedFlame = sg.findNode(player, "animatedFlame")
        animatedFlame.transform = tr.translate(0, 0.2 * np.sin(1.2 * time), 0)

        # Once the render is done, buffers are swapped, showing only the complete scene.
        glfw.swap_buffers(window)

    glfw.terminate()