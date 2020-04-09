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
    bullets = []
    explosions = []
    
    # Player data
    hp = 3
    score = 0
    xPos = 0.0
    yPos = 0.0
    time = 0
    lastShotTime = 0.0


# A class to store the data of an enemy
class Enemy:
    def __init__(self, name, ship):
        self.name = name
        self.ship = ship

    xPos = 0.0
    yPos = 0.0
    xSpeed = 1
    ySpeed = -1
    time = 0.0
    lastShotTime = 0


# A class to store the data of a bullet
class Bullet:
    def __init__(self, shape, xPos, yPos, direction):
        self.shape = shape
        self.xPos = xPos
        self.yPos = yPos
        self.direction = direction
    
    time = 0.0


# A class to store the data of an explosion
class Explosion:
    def __init__(self, shape, xPos, yPos, spawnTime):
        self.shape = shape
        self.xPos = xPos
        self.yPos = yPos
        self.spawnTime = spawnTime


# Global controller that communicates with the callback function
controller = Controller()


def on_key(window, key, scancode, action, mods):

    global controller

    if key == glfw.KEY_A:
        controller.xPos = max(-0.8, controller.xPos - 0.05)

    elif key == glfw.KEY_S:
        controller.yPos = max(-1.0, controller.yPos - 0.05)

    elif key == glfw.KEY_D:
        controller.xPos = min(0.8, controller.xPos + 0.05)

    elif key == glfw.KEY_W:
        controller.yPos = min(1.0, controller.yPos + 0.05)

    elif action != glfw.PRESS:
        return
    
    elif key == glfw.KEY_F:
        print('Alternar relleno de figuras')
        controller.fillPolygon = not controller.fillPolygon

    elif key == glfw.KEY_SPACE:

        time = glfw.get_time()

        if controller.lastShotTime == round(time, 1):
            print("Recargando...")
        else:
            controller.lastShotTime = round(time, 1)
            createBullet(controller.xPos, -0.65)

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

    sign = random.randrange(-1, 2, 2)
    enemy = Enemy(name, enemyShip)
    enemy.xSpeed = sign
    enemy.ySpeed += random.randrange(-1, 2, 1) / 10.0

    # Puts the enemy in an empty area
    xSpawn = 0.0
    for friend in controller.enemies:
        if abs(friend.xPos - xSpawn) <= 0.1:
            xSpawn += 0.2 * sign
    
    enemy.xPos = xSpawn

    return enemy


def createExplosion(xPos, yPos, spawnTime):

    global controller

    explosionShape = sf.createExplosion()
    explosion = Explosion(explosionShape, xPos, yPos, spawnTime)

    controller.explosions.append(explosion)


def createBullet(xPos, yPos, player = True):

    global controller

    bulletShape = sf.createBullet(player)
    direction = 1 if player else -1

    bullet = Bullet(bulletShape, xPos, yPos, direction)

    controller.bullets.append(bullet)


def drawBullets(pipeline, time):

    global controller

    forDeletion = []
    
    for bullet in controller.bullets:

        shape = bullet.shape
        direction = bullet.direction

        if round(time, 2) != bullet.time:
            bullet.time = round(time, 2)
            bullet.yPos += 0.01 * direction

        if not 1.0 > bullet.yPos > -1.0:
            forDeletion.append(bullet)
            continue

        if direction < 0:
    
            if abs(controller.xPos - bullet.xPos) <= 0.12:
                if abs(-0.8 - bullet.yPos) <= 0.1:

                    controller.hp -= 1
                    forDeletion.append(bullet)
                    print("Daño recibido!")
                    continue
        else:

            for enemy in controller.enemies:
                if abs(enemy.xPos - bullet.xPos) <= 0.08:
                    if abs(0.8 + enemy.yPos - bullet.yPos) <= 0.1:

                        controller.score += 1
                        forDeletion.append(enemy)
                        forDeletion.append(bullet)
                        createExplosion(enemy.xPos, 0.8 + enemy.yPos, time)
                        break

        shape.transform = tr.translate(bullet.xPos, bullet.yPos, 0)
        sg.drawSceneGraphNode(shape, pipeline, "transform")
    
    for entity in forDeletion:
        # IMPORTANT: SOMETIMES THIS CAUSES A CRASH
        # TODO: FIX IT
        if type(entity) == Bullet:
            controller.bullets.remove(entity)
        else:
            controller.enemies.remove(entity)


def drawExplosions(pipeline, time):

    global controller

    forDeletion = []

    for explosion in controller.explosions:

        shape = explosion.shape
        spawnTime = explosion.spawnTime

        position = tr.translate(explosion.xPos, explosion.yPos, 0)
        scale = spawnTime + 1 - time

        shape.transform = tr.matmul([position, tr.uniformScale(scale * 0.2)])
        sg.drawSceneGraphNode(shape, pipeline, "transform")

        if time > spawnTime + 1:
            forDeletion.append(explosion)

    for explosion in forDeletion:
        controller.explosions.remove(explosion)

# Draws the enemies on screen and animates its flames
def drawEnemies(pipeline, time):

    global controller

    length = len(controller.enemies)

    for i in range(length):
        
        random.seed()

        enemy = controller.enemies[i]
        ship = enemy.ship
       
        if round(time, 2) != enemy.time:

            enemy.time = round(time, 2)
            yPos = enemy.yPos
            xPos = enemy.xPos
            
            if yPos >= 0.0:
                enemy.ySpeed = -abs(enemy.ySpeed)
            elif yPos <= -0.3:
                enemy.ySpeed = abs(enemy.ySpeed)
            yPos += 0.005 * enemy.ySpeed
            
            if xPos >= 0.8:
                enemy.xSpeed = -1
            elif xPos <= -0.8:
                enemy.xSpeed = 1

            crash = False
            for j in range(length):
                if j == i:
                    continue
                fxPos = controller.enemies[j].xPos
                if abs(xPos + 0.1 * enemy.xSpeed - fxPos) <= 0.1:
                    enemy.xSpeed = -enemy.xSpeed
                    crash = True
                    break
            
            if not crash:
                xPos += 0.005 * enemy.xSpeed

            enemy.yPos = yPos
            enemy.xPos = xPos
        
        ship.transform = tr.translate(enemy.xPos, enemy.yPos, 0)
        sg.drawSceneGraphNode(ship, pipeline, "transform")
    
        animatedFlame = sg.findNode(ship, "animatedFlame")
        animatedFlame.transform = tr.translate(0, 0.2 * np.sin(12 * time), 0)


# Decides if the enemies are gonna shot and creates
# their bullets
def angryEnemies(time):

    for enemy in controller.enemies:

        if enemy.lastShotTime == int(time):
            continue
    
        enemy.lastShotTime = int(time)
        createBullet(enemy.xPos, 0.65 + enemy.yPos, False)

        # Advanced enemies shot more bullets
        if enemy.name.startswith("advanced"):
            createBullet(enemy.xPos + 0.05, 0.7 + enemy.yPos, False)
            createBullet(enemy.xPos- 0.05, 0.7 + enemy.yPos, False)


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
    createEnemies(2)
    player = createPlayer()
    background = sf.createBackground()

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

        time = glfw.get_time()

        # Drawing the background, its 3 layers move at different rates
        # in order to simulate 3D
        background.transform = tr.translate(0, -controller.yPos, 0)

        farLayer = sg.findNode(background, "farLayer")
        farLayer.transform = tr.translate(0, controller.yPos * 0.5, 0)

        mediumLayer = sg.findNode(background, "mediumLayer")
        mediumLayer.transform = tr.translate(0, controller.yPos * 0.25, 0)

        sg.drawSceneGraphNode(background, pipeline, "transform")

        # Drawing the explosions of defeated ships
        drawExplosions(pipeline, time)

        # Creating and drawing the enemies
        # Tries to create more enemies every 3 seconds
        if int(time) % 3 == 0 and int(time) != controller.time:
            
            controller.time = int(time)

            # Adds more enemies to keep the game challenging
            extraEnemies = int(controller.score >= 15)
            extraEnemies += int(len(controller.enemies) == 1)

            createEnemies(1 + extraEnemies)

        drawEnemies(pipeline, time)
        angryEnemies(time)

        # Drawing the bullets
        drawBullets(pipeline, time)

        # Drawing the player
        player.transform = tr.translate(controller.xPos, 0, 0)
        sg.drawSceneGraphNode(player, pipeline, "transform")

        animatedFlame = sg.findNode(player, "animatedFlame")
        animatedFlame.transform = tr.translate(0, 0.2 * np.sin(12 * time), 0)

        # Once the render is done, buffers are swapped, showing only the complete scene.
        glfw.swap_buffers(window)

    glfw.terminate()