# coding=utf-8
"""
Alexander Cuevas, CC3501, 2020-1
Solves a Laplace equation in 2D with Dirichlet and Neumann
border conditions over a square domain
"""

import numpy as np
import matplotlib.pyplot as mpl
import json
import sys


# Loads a .json file that setups the problem
if len(sys.argv) <= 1:
    print("Invalid setup data.")
    sys.exit()

with open(sys.argv[1]) as j:
    data = json.load(j)

# Problem setup
# Geometry
P = data["P"]
L = data["L"]
D = data["D"]
W = data["W"]
E = data["E"]
H1 = data["H1"]
H2 = data["H2"]

# Conditions
ambient_temperature = data["ambient_temperature"]
window_loss = data["window_loss"]  #du/dx at window
heater_power = data["heater_power"] #du/dx at heater
windows = data["windows"]

# Precision
h = 0.1

# Number of unknowns
nh = int((5 * L + 6 * W) / h) + 1
nv = int((P + D + 2 * W) / h) + 1

# The domain is a rectangle
N = nh * nv

# Functions to convert the indices from i,j to k and viceversa
# i,j indexes the discrete domain in 2D; k parametrizes i,j
def getK(i, j):
    return j * nh + i

def getIJ(k):
    i = k % nh
    j = k // nh
    return (i, j)

# Matrix of unknown coefficients
A = np.zeros((N, N))

# Vector that contais the right side of the equations
b = np.zeros((N,))


# Iterating over each point inside the domain
# Each point has an equation associated
# The equation is different depending on the point location inside the domain
for i in range(0, nh):
    for j in range(0, nv):

        #Equation associated with row k
        k = getK(i, j)

        # Indices of the other coefficients
        k_up = getK(i, j + 1)
        k_down = getK(i, j - 1)
        k_left = getK(i - 1, j)
        k_right = getK(i + 1, j)

        # Depending on the location of the point, the equation is different
        # Interior
        if 1 <= i <= nh - 2 and 1 <= j <= nv - 2:
            A[k, k_up] = 1
            A[k, k_down] = 1
            A[k, k_left] = 1
            A[k, k_right] = 1
            A[k, k] = -4
            b[k] = 0
        
        # Left
        elif i == 0 and 1 <= j <= nv - 2:
            A[k, k_up] = 1
            A[k, k_down] = 1
            A[k, k_right] = 2
            A[k, k] = -4
            b[k] = 0
        
        # Right
        elif i == nh - 1 and 1 <= j <= nv - 2:
            A[k, k_up] = 1
            A[k, k_down] = 1
            A[k, k_left] = 2
            A[k, k] = -4
            b[k] = 0
        
        # Bottom
        elif 1 <= i <= nh - 2 and j == 0:
            A[k, k_up] = 2
            A[k, k_left] = 1
            A[k, k_right] = 1
            A[k, k] = -4
            b[k] = -2 * h * heater_power * bool(int(H1 / h) <= i <= int((H1 + H2) / h))
        
        # Top
        elif 1 <= i <= nh - 2 and j == nv - 1:
            A[k, k_left] = 1
            A[k, k_right] = 1
            A[k, k] = -4

            if int(W / h) <= i <= int((L + W) / h):
                A[k, k_down] = 1 + windows[0]
                b[k] = -2 * h * window_loss if bool(windows[0]) else -ambient_temperature
            
            elif int((L + 2 * W) / h) <= i <= int(2 * (L + W) / h):
                A[k, k_down] = 1 + windows[1]
                b[k] = -2 * h * window_loss if bool(windows[1]) else -ambient_temperature
            
            elif int((2 * L + 3 * W) / h) <= i <= int(3 * (L + W) / h):
                A[k, k_down] = 1 + windows[2]
                b[k] = -2 * h * window_loss if bool(windows[2]) else -ambient_temperature
            
            elif int((3 * L + 4 * W) / h) <= i <= int(4 * (L + W) / h):
                A[k, k_down] = 1 + windows[3]
                b[k] = -2 * h * window_loss if bool(windows[3]) else -ambient_temperature
            
            elif int((4 * L + 5 * W) / h) <= i <= int(5 * (L + W) / h):
                A[k, k_down] = 1 + windows[4]
                b[k] = -2 * h * window_loss if bool(windows[4]) else -ambient_temperature

        # Corner lower left
        elif (i, j) == (0, 0):
            A[k, k_up] = 2
            A[k, k_right] = 2
            A[k, k] = -4
            b[k] = 0

        # Corner lower right
        elif (i, j) == (nh - 1, 0):
            A[k, k_up] = 2
            A[k, k_left] = 2
            A[k, k] = -4
            b[k] = 0

        # Corner upper left
        elif (i, j) == (0, nv - 1):
            A[k, k_down] = 1 + windows[0]
            A[k, k_right] = 2
            A[k, k] = -4
            b[k] = -2 * h * window_loss if bool(windows[0]) else -ambient_temperature

        # Corner upper right
        elif (i, j) == (nh - 1, nv - 1):
            A[k, k_down] = 1 + windows[4]
            A[k, k_left] = 2
            A[k, k] = -4
            b[k] = -2 * h * window_loss if bool(windows[4]) else -ambient_temperature

        else:
            print("Point (" + str(i) + ", " + str(j) + ") missed!")
            print("Associated point index is " + str(k))
            raise Exception()


# Solving the system
x = np.linalg.solve(A, b)

# Solution in the 2d discrete domain
u = np.zeros((nh, nv))

for k in range(0, N):
    i, j = getIJ(k)
    u[i, j] = x[k]

# Dirichlet boundary conditions (top side)
if not bool(windows[0]):
    u[int(W / h):int((L + W) / h) + 1, nv - 1] = ambient_temperature

if not bool(windows[1]):
    u[int((L + 2 * W) / h):int(2 * (L + W) / h) + 1, nv - 1] = ambient_temperature

if not bool(windows[2]):
    u[int((2 * L +  3 * W) / h):int(3 * (L + W) / h) + 1, nv - 1] = ambient_temperature

if not bool(windows[3]):
    u[int((3 * L + 4 * W) / h):int(4 * (L + W) / h) + 1, nv - 1] = ambient_temperature

if not bool(windows[4]):
    u[int((4 * L + 5 * W) / h):int(5 * (L + W) / h) + 1, nv - 1] = ambient_temperature

# Setting up the visualization
fig, ax = mpl.subplots(1,1)
pcm = ax.pcolormesh(u.T, cmap='RdBu_r')
fig.colorbar(pcm)
ax.set_xlabel('x')
ax.set_ylabel('y')
ax.set_title('Laplace equation solution.\n Neumann Condition at the right side.')
ax.set_aspect('equal', 'datalim')

mpl.show()