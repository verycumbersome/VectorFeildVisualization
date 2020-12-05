import os
from dataclasses import dataclass, field
import numpy as np
import glfw
import OpenGL
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

from PIL import Image

# Import opengl shapes from file
import shapes

WINDOW_W = 1500
WINDOW_H = 1500

display_mode = 1
ply = None

@dataclass
class vertex:
    x: float
    y: float
    z: float

    vx: float
    vy: float
    vz: float

    s: float

    rgb: dict = field(repr=False, default_factory=dict)


@dataclass
class face:
    count: int
    vertices: []


@dataclass
class PLY:
    vertices: list
    faces: list


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
                    int(v_info[0]),   # x
                    int(v_info[1]),   # y
                    int(v_info[2]),   # z
                    float(v_info[3]), # vx
                    float(v_info[4]), # vy
                    float(v_info[5]), # vz
                    float(v_info[6]), # s
                    {"r": 1.0, "g": 1.0, "b": 1.0}, #rgb
                )
            vertices.append(v)

        faces = []
        for i in range(n_faces):
            f_info = data.pop(0).split()
            f = face(
                    int(f_info[0]),
                    [
                        vertices[int(f_info[1])],
                        vertices[int(f_info[2])],
                        vertices[int(f_info[3])],
                        vertices[int(f_info[4])],
                    ]
                )
            faces.append(f)

        return(PLY(vertices, faces))

# def lighting():
    # glEnable(GL_DEPTH_TEST)
    # glEnable(GL_LIGHTING)
    # glEnable(GL_BLEND)
    # glLightfv(GL_LIGHT0, GL_POSITION, [10, 4, 10, 1])
    # glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 1, 0.8, 1])
    # glLightf(GL_LIGHT0, GL_CONSTANT_ATTENUATION, 0.1)
    # glLightf(GL_LIGHT0, GL_LINEAR_ATTENUATION, 0.05)
    # glEnable(GL_LIGHT0)
    # return


def read_texture(filename):
    _, file_extension = os.path.splitext(filename)
    img = Image.open(filename)
    img_data = np.array(list(img.getdata()), np.int8)
    texture_id = glGenTextures(1)

    glBindTexture(GL_TEXTURE_2D, texture_id)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)

    if (file_extension == ".jpg"):
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, img.size[0], img.size[1], 0,
                GL_RGB, GL_UNSIGNED_BYTE, img_data)

    if (file_extension == ".png"):
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.size[0], img.size[1], 0,
            GL_RGBA, GL_UNSIGNED_BYTE, img_data)

    return texture_id



def init():
    glClearColor(0.2, 0.2, 0.2, 0.0)
    glShadeModel(GL_FLAT)

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_TEXTURE_2D)

    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)

    global ply
    ply = read_ply("new_vector_data/v1.ply")
    # read_texture("texture2.jpg")


def keyboard(bkey, x, y):
    global display_mode

    key = bkey.decode("utf-8")
    if key == chr(27):
        os._exit(0)

    if key == "1":
        display_mode = 1

    if key == "2":
        display_mode = 2

    if key == "3":
        display_mode = 3

    if key == "4":
        display_mode = 4

    if key == "5":
        display_mode = 5

    if key == "q":
        os._exit(0)


def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_TEXTURE_2D)
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)

    # Set Projection window view
    glViewport(0, 0, WINDOW_H, WINDOW_W)
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, (WINDOW_H/WINDOW_W), 0.1, 50.0)
    glLoadIdentity()
    glOrtho(-20.0, 20.0, -20.0, 20.0, -100000.0, 100000.0)

    # Set Model view
    glMatrixMode(GL_MODELVIEW)

    global display_mode
    global ply

    if display_mode == 1:
        glRotatef(0.5, 1, 1, 1)
        shapes.render_ply(ply)

    if display_mode == 2:
        glRotatef(0.2, 1, 1, 1)
        shapes.render_shape(4, 4, shapes.cylinder)

    if display_mode == 3:
        glRotatef(1, 1, 1, 1)
        shapes.render_shape(10, 10, shapes.cylinder)

    if display_mode == 4:
        glRotatef(1, 1, 1, 1)
        shapes.render_shape(10, 10, shapes.sphere, 4)

    if display_mode == 5:
        glRotatef(1, 1, 1, 1)
        shapes.render_shape(10, 10, shapes.vase)

    glFlush()


def main():
    glutInit()
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_H, WINDOW_W)
    glutInitWindowPosition(100, 100)
    wind = glutCreateWindow("Surface Parameterization")

    # lighting()

    init()

    glutDisplayFunc(display)
    glutIdleFunc(display)

    glutKeyboardFunc(keyboard)
    glutMainLoop()


if __name__ == "__main__":
    main()
