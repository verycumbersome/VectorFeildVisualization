import os
import math
import numpy as np
from dataclasses import dataclass, field
# from numpy.linalg import eig, eigh, eigvals
import numpy.linalg as LA

import OpenGL
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *


@dataclass
class vertex:
    # XYZ coordinates for the vertex
    x: float
    y: float
    z: float

    # Vector field info for these points
    vx: float
    vy: float
    vz: float

    # Scalar value at vertex
    s: float

    # Size 3 dict of rgb: rgb["r"] = red_val, etc..
    rgb: dict = field(repr=False, default_factory=dict)

    def __getitem__(self, index):
        return({
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "vx": self.vx,
            "vy": self.vy,
            "vz": self.vz,
        }[index])


@dataclass
class face:
    # Number of vertices and list of all vertices for the face
    count: int
    vertices: list

    has_singularity: bool = False

    def __post_init__(self):
        self.get_vert_order()

    def get_vert_order(self):
        self.x1 = min(self.vertices, key=lambda k: k.x)
        self.x2 = max(self.vertices, key=lambda k: k.x)
        self.y1 = min(self.vertices, key=lambda k: k.y)
        self.y2 = max(self.vertices, key=lambda k: k.y)

        return ({
            "x1": self.x1, "x2": self.x2,
            "y1": self.y1, "y2": self.y2,
            })

    def get_singularity(self):
        # Get vector information at points
        fx1y1 = self.vertices[self.vertices.index(self.y1)].vx
        fx2y1 = self.vertices[(self.vertices.index(self.y1) + 1) % 4].vx
        fx2y2 = self.vertices[(self.vertices.index(self.y1) + 2) % 4].vx
        fx1y2 = self.vertices[(self.vertices.index(self.y1) + 3) % 4].vx

        gx1y1 = self.vertices[self.vertices.index(self.y1)].vy
        gx2y1 = self.vertices[(self.vertices.index(self.y1) + 1) % 4].vy
        gx2y2 = self.vertices[(self.vertices.index(self.y1) + 2) % 4].vy
        gx1y2 = self.vertices[(self.vertices.index(self.y1) + 3) % 4].vy

        # Calculate quadratic to find s1, s2 and t
        a00 = fx1y1
        a10 = fx2y1 - fx1y1
        a01 = fx1y2 - fx1y1
        a11 = fx1y1 - fx2y1 - fx1y2 + fx2y2

        b00 = gx1y1
        b10 = gx2y1 - gx1y1
        b01 = gx1y2 - gx1y1
        b11 = gx1y1 - gx2y1 - gx1y2 + gx2y2

        c00 = a11 * b00 - a00 * b11
        c10 = a11 * b10 - a10 * b11
        c01 = a11 * b01 - a01 * b11

        A = (-a11 * c10)
        B = (-a11 * c00 - a01 * c10 + a10 * c01)
        C = (a00 * c01 - a01 * c00)

        # Find quadratic solution
        quad_solution = solve_quadratic(A, B, C)

        # Linearly interpolate to find singularity
        singularities = []
        for s in quad_solution:
            t = (-c00 / c01) - (c10 / c01) * s
            if (s > 0 and s < 1) and (t > 0 and t < 1):
                singularities.append((
                    linearly_interpolate(0, 1, self.x1.x, self.x2.x, s),
                    linearly_interpolate(0, 1, self.y1.y, self.y2.y, t),
                    # linearly_interpolate(0, 1, self.y1.z, self.y2.z, 0)
                    0,
                ))

        self.has_singularities = bool(len(singularities))

        return(singularities)


    def classify_singularity(self, singularity):
        dir_vec = []
        x = singularity[0]
        y = singularity[1]

        for vec in ["vx", "vy"]:
            fx1y1 = self.vertices[self.vertices.index(self.y1)][vec]
            fx2y1 = self.vertices[(self.vertices.index(self.y1) + 1) % 4][vec]
            fx2y2 = self.vertices[(self.vertices.index(self.y1) + 2) % 4][vec]
            fx1y2 = self.vertices[(self.vertices.index(self.y1) + 3) % 4][vec]

            x1, x2, y1, y2 = self.x1.x, self.x2.x, self.y1.y, self.y2.y

            # Get fx
            dir_x = (-1)/(x2 - x1) * (y2 - y)/(y2 - y1) * fx1y1 + \
                    (1)/(x2 - x1) * (y2 - y)/(y2 - y1) * fx2y1 + \
                    (-1)/(x2 - x1) * (y - y1)/(y2 - y1) * fx1y2 + \
                    (1)/(x2 - x1) * (y - y1)/(y2 - y1) * fx2y2

            # Get fy
            dir_y = (x2 - x)/(x2 - x1) * (-1)/(y2 - y1) * fx1y1 + \
                    (x - x1)/(x2 - x1) * (-1)/(y2 - y1) * fx2y1 + \
                    (x2 - x)/(x2 - x1) * (1)/(y2 - y1) * fx1y2 + \
                    (x - x1)/(x2 - x1) * (1)/(y2 - y1) * fx2y2

            # Add fx/gx and fy/gy
            dir_vec.append([dir_x, dir_y])

        # Convert fx/gx fy/gy matrix to numpy to calculate eigenvalues
        dir_vec = np.array(dir_vec)

        eig_vals = LA.eigvals(dir_vec)
        eig_vals_complex, _ = LA.eigvalsh(dir_vec)

        # print("\n\nIteration:")
        # print(dir_vec)
        # print(eig_vals)

        if eig_vals[0] > 0:
            if eig_vals[1] > 0:
                return("nodal_source")
            else:
                return("saddle_point")

        else:
            if eig_vals[1] > 0:
                return("saddle_point")
            else:
                return("nodal_sink")

@dataclass
class polyline:
    # All coordinates for the streamline
    vertices: list

    def render_streamline(self):
        glBegin(GL_LINES)
        for s in self.vertices:
            glVertex3fv(s)
        glEnd()

@dataclass
class poly:
    # All verts and faces for the polygon
    vertices: list
    faces: list

    # List of all streamlines
    streamlines: list = field(repr=False, default_factory=list)

    # Dict of all colors by classification
    sing_classes: dict = field(repr=False, default_factory=dict)

    def __post_init__(self):
        # Gets all rgb values for classification
        self.sing_classes = {
                "nodal_source":map(lambda x: x/255.0, (249, 249, 249)),
                "nodal_sink":map(lambda x: x/255.0, (255, 224, 172)),
                "saddle_point":map(lambda x: x/255.0, (255, 172, 183)),
                "center":map(lambda x: x/255.0, (104, 134, 197)),
                "focus":map(lambda x: x/255.0, (90, 164, 105)),
            }
        # Maps tuple for each color calue
        self.sing_classes = {k:tuple(v) for k, v in self.sing_classes.items()}

        # Get max and min vertices for poly
        max_xyz = [0, 0, 0]
        min_xyz = [0, 0, 0]

        for v in self.vertices:
            if max_xyz[0] < v.x:
                max_xyz[0] = v.x
            if max_xyz[1] < v.y:
                max_xyz[1] = v.y
            if max_xyz[2] < v.z:
                max_xyz[2] = v.z
            if min_xyz[0] > v.x:
                min_xyz[0] = v.x
            if min_xyz[1] > v.y:
                min_xyz[1] = v.y
            if min_xyz[2] > v.z:
                min_xyz[2] = v.z
        self.max_xyz, self.min_xyz = max_xyz, min_xyz

    def get_dir(self, coords):
        """
        Gets the direction of point on the poly
        Output: (dir_x, dir_y, dir_z) - normalized vec in direction at coords
        """
        x, y, z = coords[0], coords[1], coords[2]
        dir_vec = []

        # Iterate through faces until x is found within face vertices
        for face in self.faces:
            v = face.get_vert_order()

            if (x <= v["x2"].x and x >= v["x1"].x
                and y <= v["y1"].y and y <= v["y1"].y):
                break

        # Linearly interpolate between face vertices to find vx vy at x, y, z
        for vec in ["vx", "vy"]:
            fx1y1 = face.vertices[face.vertices.index(v["y1"])][vec]
            fx2y1 = face.vertices[(face.vertices.index(v["y1"]) + 1) % 4][vec]
            fx2y2 = face.vertices[(face.vertices.index(v["y1"]) + 2) % 4][vec]
            fx1y2 = face.vertices[(face.vertices.index(v["y1"]) + 3) % 4][vec]

            x1, x2, y1, y2 = v["x1"].x, v["x2"].x, v["y1"].y, v["y2"].y

            dir_v = (x2 - x)/(x2 - x1) * (y2 - y)/(y2 - y1) * fx1y1 + \
                    (x - x1)/(x2 - x1) * (y2 - y)/(y2 - y1) * fx2y1 + \
                    (x2 - x)/(x2 - x1) * (y - y1)/(y2 - y1) * fx1y2 + \
                    (x - x1)/(x2 - x1) * (y - y1)/(y2 - y1) * fx2y2

            dir_vec.append(dir_v)

        # Normalize direction
        dir_vec.append(z)
        dir_vec = np.array(dir_vec)
        dir_vec = dir_vec / np.sqrt(np.sum(dir_vec**2))

        return(dir_vec)

    def calculate_streamline(self, coords):
        """Calculate the streamline for a poly given coordinates"""
        x, y, z = coords[0], coords[1], coords[2]
        step = 0.05
        count = 400

        streamline = []

        for i in [1, -1]:
            curr = np.array([x, y, z])

            for j in range(count):
                # If calculated value is out of bounds return nothing
                if (curr[0] > self.max_xyz[0] or curr[1] > self.max_xyz[1]
                                              or curr[2] > self.max_xyz[2]):
                    break

                if (curr[0] < self.min_xyz[0] or curr[1] < self.min_xyz[1]
                                              or curr[2] < self.min_xyz[2]):
                    break
                glVertex3fv(tuple(curr))
                streamline.append(tuple(curr))
                curr = curr + self.get_dir(curr) * i * step
                streamline.append(tuple(curr))
                glVertex3fv(tuple(curr))

        self.streamlines.append(polyline(streamline))

    def calculate_singularities(self):
        """Calculate and find all the singularities for a given poly"""
        self.singularities = []

        for face in self.faces:
            for s in face.get_singularity():
                # Classification for singularity
                c = face.classify_singularity(s)

                self.singularities.append({
                    "type":c,
                    "coordinates":s,
                    "rgb":self.sing_classes[c],
                })


    def render_singularities(self):
        glPointSize(10.0)
        glBegin(GL_POINTS)
        for s in self.singularities:
            glColor3f(s["rgb"][0], s["rgb"][1], s["rgb"][2])
            glVertex3fv(s["coordinates"])

        glEnd()
        glPointSize(2.0)

    def render_streamlines(self):
        for s in self.singularities:
            self.calculate_streamline(s["coordinates"])
            for p in self.streamlines:
                p.render_streamline()
            # s.render_streamline()


def linearly_interpolate(a, b, M, m, v):
    """Interpolate between m and M with a range of [a, b] and input v"""
    return((b - a) * ((v - m)/(M - m)) + a)


def solve_quadratic(A, B, C):
    """Solve quadratic equation given A, B, and C"""
    if (A == 0):
        return([])

    discriminant = ((B ** 2) - 4*A*C)
    if discriminant > 0:
        s1 = (-B + math.sqrt(discriminant)) / (2*A)
        s2 = (-B - math.sqrt(discriminant)) / (2*A)
        return([s1, s2])

    elif (discriminant == 0):
        return((-B + math.sqrt(discriminant)) / (2*A))

    else:
        return([])


def read_ply(filename):
    """
    Read and parse a PLY file
    Output: PLY(vertices, faces) - vertices and faces parsed from file
    """
    with open(filename, "r") as ply_file:
        header = ply_file.read().split("end_header")
        header, data = header[0], header[1][1:].split("\n")

        n_verts = [x for x in header.split("\n") if "element vertex" in x][0]
        n_faces = [x for x in header.split("\n") if "element face" in x][0]

        n_verts = int(n_verts.split()[-1])
        n_faces = int(n_faces.split()[-1])

        vertices = []
        for i in range(n_verts):
            v_info = data.pop(0).split()

            v = vertex(
                    int(v_info[0]),    # x
                    int(v_info[1]),    # y
                    int(v_info[2]),    # z
                    float(v_info[3]),  # vx
                    float(v_info[4]),  # vy
                    float(v_info[5]),  # vz
                    float(v_info[6]),  # s
                    {"r": 1.0, "g": 1.0, "b": 1.0},  #rgb
                )
            vertices.append(v)

        faces = []
        for i in range(n_faces):
            f_info = data.pop(0).split()
            f = face(
                    int(f_info[0]),
                    [
                        vertices[int(f_info[1])], # v1
                        vertices[int(f_info[2])], # v2
                        vertices[int(f_info[3])], # v3
                        vertices[int(f_info[4])], # v4
                    ]
                )
            faces.append(f)

        return(poly(vertices, faces))
