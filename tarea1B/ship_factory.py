"""
Alexander Cuevas, CC3501, 2020-1
Ship factory that builds spaceships
and provides ammunition, it works 
for both sides. (o_o)
"""

import glfw
import math
import numpy as np

# Local imports
import transformations as tr
import basic_shapes as bs
import scene_graph as sg
import easy_shaders as es

# Local imports (created by me)
import visual_effects as ve


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

    gpuGrayTrapeze = es.toGPUShape(ve.createColorTrapeze(0.6, 0.6, 0.6))

    gpuBlueTriangle = es.toGPUShape(ve.createColorTriangle(0.2, 0.5, 1))
    gpuWhiteTriangle = es.toGPUShape(ve.createColorTriangle(1, 1, 1))

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

    gpuGrayTriangle = es.toGPUShape(ve.createColorTriangle(0.4, 0.6, 0.4))

    gpuGrayTrapeze = es.toGPUShape(ve.createColorTrapeze(0.6, 0.8, 0.6))
    gpuYellowTrapeze = es.toGPUShape(ve.createColorTrapeze(1, 1, 0))

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
    # advanced ships and they had a slighty different model
    channel =  1- int(advanced)

    gpuVariantTriangle = es.toGPUShape(ve.createColorTriangle(channel, 0.6, 0))

    gpuBlueTrapeze = es.toGPUShape(ve.createColorTrapeze(0, 0, 1))
    gpuVariantTrapeze0 = es.toGPUShape(ve.createColorTrapeze(channel, 1 - channel, 0))
    gpuVariantTrapeze1 = es.toGPUShape(ve.createColorTrapeze(channel, 0.4, 0))
    
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


# Creates a green bullet
# If "player", creates a yellow bullet instead
def createBullet(player = True):

    gpuVariantCube = es.toGPUShape(bs.createColorCube(int(player), 1, 0))

    littleBullet = sg.SceneGraphNode("littleBullet")
    littleBullet.transform = tr.matmul([tr.rotationZ(math.pi / 4), tr.uniformScale(0.05)])
    littleBullet.childs += [gpuVariantCube]

    bullet = sg.SceneGraphNode("bullet")
    bullet.childs += [littleBullet]

    return bullet
