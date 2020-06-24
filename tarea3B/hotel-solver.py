# coding=utf-8
"""
Alexander Cuevas, CC3501, 2020-1
Solves a Laplace equation in 2D with Dirichlet and Neumann
border conditions over a rectangular domain
"""

import numpy as np
import matplotlib.pyplot as mpl
import json
import sys

# Imports from scipy in order to use a sparse matrix
from scipy.sparse import csc_matrix
from scipy.sparse.linalg import spsolve


# Loads a .json file that setups the problem
if len(sys.argv) <= 1:
    print("Invalid setup data.")
    sys.exit()

name = sys.argv[1]

with open(name) as j:
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
window_loss = -data["window_loss"] #du/dx at window
heater_power = data["heater_power"] #du/dx at heater
windows = data["windows"]

# Precision
h = 0.1

# Number of unknowns
nh = int((5 * L + 4 * W) / h) + 1
nv = int((P + D + W) / h) + 1

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

# Transforms a measure into a valid index
def idx(value):
    global h
    return int(value / h + 0.0001)

# 0 - 1 - 2
# 3 - 4 - 5
# 6 - 7 - 8
# Checks where a value is related to 2 vertical boundaries
# and a list of 2 horizontal boundaries
def boundary_check(i, j, xs, ys):
    for idx in range(0, len(xs), 2):
        if xs[idx] == i and ys[0] == j:
            return 6
        if xs[idx] == i and ys[0] < j < ys[1]:
            return 3
        if xs[idx] == i and j == ys[1]:
            return 0
        if xs[idx] < i < xs[idx + 1] and ys[0] == j:
            return 7
        if xs[idx] < i < xs[idx + 1] and ys[0] < j < ys[1]:
            return 4
        if xs[idx] < i < xs[idx + 1] and j == ys[1]:
            return 1
        if i == xs[idx + 1] and ys[0] == j:
            return 8
        if i == xs[idx + 1] and ys[0] < j < ys[1]:
            return 5
        if i == xs[idx + 1] and j == ys[1]:
            return 2
    return -1

# Assings values to M according to the mode used
def asign(M, k, kls, mode):
    if mode == 4:
        M[k, k] = -1
        return
    M[k, kls[0]] = 1 + int(mode == 1) - int(mode == 7)
    M[k, kls[1]] = 1 + int(mode == 7) - int(mode == 1)
    M[k, kls[2]] = 1 + int(mode == 3) - int(mode == 5)
    M[k, kls[3]] = 1 + int(mode == 5) - int(mode == 3)
    M[k, k] = -4

# Sets the correct values of a window
def set_window(M, m, k, kls, i, closed, ls):
    global window_loss
    global ambient_temperature

    if closed:
        M[k, kls[1]] = 2
        M[k, kls[2]] = 1 + int(i == ls[1]) - int(i == ls[0])
        M[k, kls[3]] = 1 + int(i == ls[0]) - int(i == ls[1])
        M[k, k] = -4
        m[k] = -2 * h * window_loss
    else:
        m[k] = -ambient_temperature
    
        #Equation associated with j - 1
        k = getK(i, j - 1)
        A[k, getK(i, j)] = 0
        b[k] = -ambient_temperature


# Matrix of unknown coefficients
A = np.zeros((N, N))

# Vector that contais the right side of the equations
b = np.zeros((N,))

# Constants that are used over and over in the iterarion
parallel_xs = [0, idx(L - E), idx(L), idx(2 * L + W - E), idx(2 * L + W), idx(3 * L + 2 * W - E)]
parallel_xs += [idx(3 * L + 2 * W), idx(4 * L + 3 * W - E), idx(4 * L + 3 * W), idx(5 * L + 4 * W - E)]
parallel_ys = [idx(P), idx(P + W)]

perpendicular_xs = [idx(L), idx(L + W), idx(2 * L + W), idx(2 * (L + W))]
perpendicular_xs += [idx(3 * L + 2 * W), idx(3 * (L + W)), idx(4 * L + 3 * W), idx(4 * (L + W))]
perpendicular_ys = [idx(P), nv - 1]

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
        kls = [k_up, k_down, k_left, k_right]

        # Depending on the location of the point, the equation is different
        # Interior
        if 1 <= i <= nh - 2 and 1 <= j <= nv - 2:

            # Checks if the point is in an interior wall
            parallel = boundary_check(i, j, parallel_xs, parallel_ys)
            if parallel > 1:
                asign(A, k, kls, parallel)
            else:
                perpendicular = boundary_check(i, j, perpendicular_xs, perpendicular_ys)
                if parallel == 1 and perpendicular == -1:
                    asign(A, k, kls, parallel)
                elif parallel == 1 and perpendicular == 5:
                    A[k, k_up] = 2
                    A[k, k_right] = 2
                    A[k, k] = -4
                else:
                    asign(A, k, kls, perpendicular)
        
        # Left
        elif i == 0 and 1 <= j <= nv - 2:
            A[k, k] = -4

            if j == idx(P):
                A[k, k_down] = 2
                A[k, k_right] = 2
            elif j == idx(P + W):
                A[k, k_up] = 2
                A[k, k_right] = 2
            elif idx(P) < j < idx(P + W):
                asign(A, k, kls, 4)
            else:
                asign(A, k, kls, 5)
        
        # Right
        elif i == nh - 1 and 1 <= j <= nv - 2:
            asign(A, k, kls, 3)
        
        # Bottom
        elif 1 <= i <= nh - 2 and j == 0:
            asign(A, k, kls, 1)
            b[k] = -2 * h * heater_power * bool(idx(H1) <= i <= idx(H1 + H2))
        
        # Top
        elif 1 <= i <= nh - 2 and j == nv - 1:
            A[k, k] = -1

            if 1 <= i <= idx(L):
                set_window(A, b, k, kls, i, bool(windows[0]), [1, idx(L)])
            
            elif idx(L + W) <= i <= idx(2 * L + W):
                set_window(A, b, k, kls, i, bool(windows[1]), [idx(L + W), idx(2 * L + W)])
            
            elif idx(2 * (L + W)) <= i <= idx(3 * L + 2 * W):
                set_window(A, b, k, kls, i, bool(windows[2]), [idx(2 * (L + W)), idx(3 * L + 2 * W)])
            
            elif idx(3 * (L + W)) <= i <= idx(4 * L + 3 * W):
                set_window(A, b, k, kls, i, bool(windows[3]), [idx(3 * (L + W)), idx(4 * L + 3 * W)])
            
            elif idx(4 * (L + W)) <= i <= idx(5 * L + 4 * W):
                set_window(A, b, k, kls, i, bool(windows[4]), [idx(4 * (L + W)), idx(5 * L + 4 * W)])

        # Corner lower left
        elif (i, j) == (0, 0):
            A[k, k_up] = 2
            A[k, k_right] = 2
            A[k, k] = -4

        # Corner lower right
        elif (i, j) == (nh - 1, 0):
            A[k, k_up] = 2
            A[k, k_left] = 2
            A[k, k] = -4

        # Corner upper left
        elif (i, j) == (0, nv - 1):
            if bool(windows[0]):
                A[k, k_down] = 2
                A[k, k_right] = 2
                A[k, k] = -4
                b[k] = -2 * h * window_loss
            else:
                A[k, k] = -1
                b[k] = -ambient_temperature

                k2 = getK(i, j - 1)
                A[k2, getK(i, j)] = 0
                b[k2] = -ambient_temperature

        # Corner upper right
        elif (i, j) == (nh - 1, nv - 1):
            if bool(windows[4]):
                A[k, k_down] = 2
                A[k, k_left] = 2
                A[k, k] = -4
                b[k] = -2 * h * window_loss
            else:
                A[k, k] = -1
                b[k] = -ambient_temperature

                k2 = getK(i, j - 1)
                A[k2, getK(i, j)] = 0
                b[k2] = -ambient_temperature

        else:
            print("Point (" + str(i) + ", " + str(j) + ") missed!")
            print("Associated point index is " + str(k))
            raise Exception()


# Solving the system
print("Solving the problem...")
x = spsolve(csc_matrix(A), b)

# Solution in the 2d discrete domain
u = np.zeros((nh, nv))

for k in range(0, N):
    i, j = getIJ(k)
    u[i, j] = x[k]

# Setting up the visualization (optional)
if False:
    fig, ax = mpl.subplots(1,1)
    pcm = ax.pcolormesh(u.T, cmap='RdBu_r')
    fig.colorbar(pcm)
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_title('Laplace equation solution.')
    ax.set_aspect('equal', 'datalim')

    mpl.show()

# Saving the matrix
solution_name = name[:name.index(".")] + '_solution.npy'
with open(solution_name, 'wb') as solution:
    np.save(solution, u)

print("Problem solved, solution stored in: " + solution_name)