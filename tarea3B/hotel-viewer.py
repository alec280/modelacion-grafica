# coding=utf-8
"""
Alexander Cuevas, CC3501, 2020-1
Visualizes the solution of a Laplace equation using 3D
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