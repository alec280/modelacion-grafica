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
import visual_effects as ve
import ship_factory as sf


# Input from command line
N = sys.argv[1] if len(sys.argv) > 1 else "60"
N = int(N) if N.isdigit() else 60


# A class to store variables affected by the user's input
class Controller:
    xPos = 0.0
    yPos = 0.0


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
    lastShotTime = 0.0


# A class to store the data of a bullet
# Bullets are always an element of a global list
class Bullet:

    global logic

    def __init__(self, yellow, xPos, yPos):
        self.shape = sf.createBullet(yellow)
        self.direction = 1 if yellow else -1
        self.xPos = xPos
        self.yPos = yPos
        self.time = 0.0

        logic.bullets.append(self)


# A class to store the data of an explosion
# Explosions are always an element of a global list
class Explosion:

    global logic

    def __init__(self, xPos, yPos, spawnTime):
        self.shape = ve.createExplosion()
        self.xPos = xPos
        self.yPos = yPos
        self.spawnTime = spawnTime

        logic.explosions.append(self)


# A class to store global variables
class Logic:
    score = 0
    fleet = 0

    # Properties of the player's ship
    hp = 3
    lastShotTime = 0.0
    impactTime = -1.0
    globalTime = 0

    # List of objects
    enemies = []
    bullets = []
    explosions = []

# Global controller that communicates with the callback function
controller = Controller()

# Global variable that stores the data of the game
logic = Logic()


# Handles the input of the user
def on_key(window, key, scancode, action, mods):

    global controller
    global logic

    # Closing the game is the only input 
    # accepted once the game is over
    if logic.hp <= 0 or logic.score >= N:
        if action == glfw.PRESS and key == glfw.KEY_ESCAPE:
            sys.exit()
        else:
            print('Tecla desconocida')

    elif key == glfw.KEY_A:
        controller.xPos = max(-0.85, controller.xPos - 0.05)

    elif key == glfw.KEY_S:
        controller.yPos = max(-0.05, controller.yPos - 0.05)

    elif key == glfw.KEY_D:
        controller.xPos = min(0.85, controller.xPos + 0.05)

    elif key == glfw.KEY_W:
        controller.yPos = min(0.25, controller.yPos + 0.05)

    elif action != glfw.PRESS:
        return
    
    elif key == glfw.KEY_SPACE:

        time = glfw.get_time()

        if logic.lastShotTime + 0.2 > time:
            print("Recargando...")
        else:
            logic.lastShotTime = time
            Bullet(True, controller.xPos, -0.65 + controller.yPos)

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

    global logic

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
    for friend in logic.enemies:
        if abs(friend.xPos - xSpawn) <= 0.1:
            xSpawn += 0.2 * sign
    
    enemy.xPos = xSpawn

    return enemy


# Updates the position of the bullets and determines
# if a ship suffered damage
def bulletLogic(time):

    global logic
    global controller

    forDeletion = []
    
    for bullet in logic.bullets:

        direction = bullet.direction
        yPos = bullet.yPos

        if round(time, 2) != bullet.time:
            bullet.time = round(time, 2)
            bullet.yPos += 0.01 * direction

        # Deleting bullets that won't be drawn
        if not 1.0 > yPos > -1.0:
            forDeletion.append(bullet)
            continue
        
        # Nothing happens in the middle of the screen
        if 0.5 > yPos > -0.45:
            continue

        # Using the bullet against the player
        if direction < 0:
            if abs(controller.xPos - bullet.xPos) <= 0.12:
                if abs(yPos + 0.8 - controller.yPos) <= 0.1:
                        
                    # The player has invulnerability frames
                    if logic.impactTime + 1.0 < time:
                        logic.hp -= 1
                        logic.impactTime = time
                        print("Daño recibido!")

                    forDeletion.append(bullet)
            continue
        
        # Using the bullet against one enemy
        for enemy in logic.enemies:
            if abs(enemy.xPos - bullet.xPos) <= 0.08:
                if abs(0.8 + enemy.yPos - yPos) <= 0.1:

                    forDeletion.append(bullet)
                    Explosion(enemy.xPos, 0.8 + enemy.yPos, time)
                    logic.enemies.remove(enemy)

                    # Updating the score
                    logic.score += 1
                    if logic.score > 0:
                        text = f"SPACE WAR (Score: {logic.score})"
                        glfw.set_window_title(window, text)

                    break

    for bullet in forDeletion:
        logic.bullets.remove(bullet)


# The explosions eventually disappear
def explosionLogic(time):

    global logic
    forDeletion = []

    for explosion in logic.explosions:
        if time > explosion.spawnTime + 1:
            forDeletion.append(explosion)

    for explosion in forDeletion:
        logic.explosions.remove(explosion)


# Moves the enemies and creates their bullets
def enemyLogic(time):

    global logic

    length = len(logic.enemies)

    for i in range(length):
        
        enemy = logic.enemies[i]
       
        if round(time, 2) != enemy.time:

            enemy.time = round(time, 2)
            yPos = enemy.yPos
            xPos = enemy.xPos

            crash = False
            
            # Updating the vertical position
            if yPos >= 0.05:
                enemy.ySpeed = -abs(enemy.ySpeed)
            elif yPos <= -0.25:
                enemy.ySpeed = abs(enemy.ySpeed)
            yPos += 0.005 * enemy.ySpeed
            
            # Updating the horizontal position
            if xPos >= 0.9:
                enemy.xSpeed = -1
            elif xPos <= -0.9:
                enemy.xSpeed = 1

            # The enemies don't want to crash with each other
            for j in range(length):
                if j == i:
                    continue
                fxPos = logic.enemies[j].xPos
                if abs(xPos + 0.1 * enemy.xSpeed - fxPos) <= 0.1:
                    enemy.xSpeed = -enemy.xSpeed
                    crash = True
                    break
            
            if not crash:
                xPos += 0.005 * enemy.xSpeed

            enemy.yPos = yPos
            enemy.xPos = xPos
        
        # Deciding if the enemy is going to shot
        waitingTime = 1.0 - 0.25 * min(2, logic.score // 25)

        if enemy.lastShotTime + waitingTime > time:
            continue
    
        enemy.lastShotTime = time
        Bullet(False, enemy.xPos, 0.65 + enemy.yPos)

        # Advanced enemies shot more bullets
        if enemy.name.startswith("advanced"):
            Bullet(False, enemy.xPos + 0.05, 0.7 + enemy.yPos)
            Bullet(False, enemy.xPos - 0.05, 0.7 + enemy.yPos)


# Creates "n" enemies, some enemies are stronger than others
def createEnemies(n):

    global logic

    if logic.fleet == N or len(logic.enemies) == 4:
        return

    for _ in range(n):

        # Increases the fleet counter, which also increases
        # the difficulty of the game
        logic.fleet += 1
        i = logic.fleet
        enemies = logic.enemies

        # Creates a stronger enemy to keep the game challenging
        # if the fleet is high enough
        advanced = i % max(1, 5 - logic.fleet // 15) == 0

        # Creates a new enemy with a unique name
        enemy = createEnemy(advanced)
        enemy.name += str(i - 1)
        enemies.append(enemy)

        # There can only be 4 enemies on screen
        if len(enemies) == 4 or i == N:
            break


# Updates the game according to time and logic
def gameFlow(time):
    
    explosionLogic(time)
    enemyLogic(time)
    bulletLogic(time)


# Draws a lifebar that reflects the player's health
def drawLifeBar(pipeline, hp):

    bar0 = ve.createLifeBar(hp > 0)
    bar0.transform = tr.translate(-0.92, -0.95, 0)

    bar1 = ve.createLifeBar(hp > 1)
    bar1.transform = tr.translate(-0.81, -0.95, 0)

    bar2 = ve.createLifeBar(hp > 2)
    bar2.transform = tr.translate(-0.70, -0.95, 0)

    sg.drawSceneGraphNode(bar0, pipeline, "transform")
    sg.drawSceneGraphNode(bar1, pipeline, "transform")
    sg.drawSceneGraphNode(bar2, pipeline, "transform")


# Draws the explosions of defeated ships
def drawExplosions(time):

    global logic

    for explosion in logic.explosions:
        shape = explosion.shape
        spawnTime = explosion.spawnTime

        position = tr.translate(explosion.xPos, explosion.yPos, 0)
        scale = tr.uniformScale(0.2 * (spawnTime + 1 - time))

        shape.transform = tr.matmul([position, scale])
        sg.drawSceneGraphNode(shape, pipeline, "transform")


# Draws everything on the screen
def drawScreen(pipeline, time, background, player):

    global controller
    global logic

    # Local position of the animated flames
    flameLoop = 0.2 * np.sin(12 * time)
    
    # Drawing the animated background.
    backTime = time % 5
    background.transform = tr.translate(0, -backTime * 0.4, 0)
    sg.drawSceneGraphNode(background, pipeline, "transform")

    # Drawing the explosions of defeated ships
    drawExplosions(time)

    # Drawing the enemies
    for enemy in logic.enemies:
        ship = enemy.ship
        ship.transform = tr.translate(enemy.xPos, enemy.yPos, 0)

        animatedFlame = sg.findNode(ship, "animatedFlame")
        animatedFlame.transform = tr.translate(0, flameLoop, 0)

        sg.drawSceneGraphNode(ship, pipeline, "transform")

    # Drawing the bullets
    for bullet in logic.bullets:
        shape = bullet.shape
        shape.transform = tr.translate(bullet.xPos, bullet.yPos, 0)
        sg.drawSceneGraphNode(shape, pipeline, "transform")

    # Drawing the player
    player.transform = tr.translate(controller.xPos, controller.yPos, 0)

    animatedFlame = sg.findNode(player, "animatedFlame")
    animatedFlame.transform = tr.translate(0, flameLoop, 0)

    sg.drawSceneGraphNode(player, pipeline, "transform")

    # Drawing the lifebar of the player, with the corresponding colors
    drawLifeBar(pipeline, logic.hp)


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

    # Assembling the shader programs (pipeline) with both shaders
    pipeline = es.SimpleTransformShaderProgram()
    texturePipeline = es.SimpleTextureTransformShaderProgram()
    
    # Telling OpenGL to use our shader program
    glUseProgram(pipeline.shaderProgram)

    # Setting up the clear screen color
    glClearColor(0.0, 0.0, 0.0, 1.0)

    # Creating shapes on GPU memory
    createEnemies(2)
    player = createPlayer()
    background = ve.createBackground()
    gameOver = ve.createGameOver()
    victory = ve.createGameOver(True)

    while not glfw.window_should_close(window):
        
        time = glfw.get_time()

        # Using GLFW to check for input events
        glfw.poll_events()

        # Clearing the screen in both, color and depth
        glClear(GL_COLOR_BUFFER_BIT)

        # If the game is over, the loop is reduced to
        # showing a victory or defeat texture
        if logic.hp <= 0 or logic.score >= N: 

            logic.bullets.clear()
            logic.enemies.clear()

            glUseProgram(texturePipeline.shaderProgram)
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

            image = victory if logic.score >= N else gameOver

            image.transform = tr.uniformScale(1 + 0.1 * np.sin(5 * time))
            sg.drawSceneGraphNode(image, texturePipeline, "transform")

            # If just defeated, draws a single explosion
            if logic.hp == 0:
                logic.explosions.clear()
                Explosion(controller.xPos, -0.8 + controller.yPos, time)
                logic.hp -= 1
            
            if len(logic.explosions) > 0:
                glUseProgram(pipeline.shaderProgram)
                explosionLogic(time)
                drawExplosions(time)

            glfw.swap_buffers(window)
            continue
        
        # Filling or not the shapes
        # it only shows lines to indicate invulnerability frames
        if logic.impactTime + 1.0 > time:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        # Creating and drawing the enemies
        # Tries to create more enemies every 3 seconds
        if int(time) % 3 == 0 and int(time) != logic.globalTime:
            
            logic.globalTime = int(time)

            # Tries to add more enemies to keep the game challenging
            extraEnemies = int(len(logic.enemies) < 2)
            extraEnemies += int(logic.score > 15)

            createEnemies(1 + extraEnemies)

        # Updating the game state
        gameFlow(time)

        # Drawing everything on screen
        drawScreen(pipeline, time, background, player)

        # Once the render is done, buffers are swapped, showing only the complete scene.
        glfw.swap_buffers(window)

    glfw.terminate()