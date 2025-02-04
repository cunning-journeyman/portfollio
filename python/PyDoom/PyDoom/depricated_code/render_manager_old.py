from math import cos, sin, pi

import pygame as pg
from PyDoom import logger
from PyDoom.globals import *


def points_in_circum(offset=0, radius=100, n=100):
    """
    Returns a list of (x, y) points offset from 0, 0 based on self.pos
    These coordinates are the circumference of a circle

    ARGS:
    @ param r = Radius in pixels
    @ param n = number of divisions, meaning the frequency of points along the circumfrence.

    RETURNS:
        List of (x, y) points
    """
    return [((cos(2 * pi / n * x) * radius + offset),
             (sin(2 * pi / n * x) * radius + offset))
            for x in range(0, n + 1)]


def draw(g, s):
    # localise these vars as it's more clear plus python accesses local variables faster
    # Expand player position for clarity
    player_pos_x = g.player.pos.x
    player_pos_y = g.player.pos.y
    player_angle = g.player.angle
    player_fov = g.player.fov
    cast_list = []

    # print(player_pos_x, player_pos_y, player_angle, player_fov, SCREEN_WIDTH, *g.level.walls[1:])
    """
    NEW PLAN!
    Instead of needlessly iterating over each pixel and messing with calculating each pixel's distance
    Why not just get the distance to each wall, then draw gradients between those wall points????
    
    """

    for i in range(int(SCREEN_WIDTH)):
        if i % 10:
            continue
        # Get the angle we want to cast to
        ray_angle = (player_angle - player_fov / 2.0) + float(i) / float(SCREEN_WIDTH) * player_fov

        # The line representing where the cast is evaluating
        player_line = ((player_pos_x, player_pos_y),
                       (player_pos_x + sin(ray_angle) * RENDER_DEPTH,
                        player_pos_y + cos(ray_angle) * RENDER_DEPTH))

        distances = [RENDER_DEPTH]
        walls = [0]

        for wall in g.level.walls[1:]:
            #
            # This is very slow to collect all the data we need to draw a frame.
            # Perhaps I can use C++ to build the data i need then unpack it in python is some way?
            # Looks like it's possible
            # https://docs.python.org/3/extending/extending.html
            #
            test = line_intersection(Line(*player_line), wall)
            if not test:
                continue
            distance = distance_to_point((player_pos_x, player_pos_y), test)
            distances.append(distance)
            walls.append(wall)

        # The distance we've found to the wall we're looking at
        distance_to_wall = min(distances)
        target_wall = walls[distances.index(distance_to_wall)]

        # Calculate the top of the walls based off the screen
        ceiling = (SCREEN_HEIGHT / 2.0) - SCREEN_HEIGHT / distance_to_wall

        # Calc the floor
        floor = SCREEN_HEIGHT - ceiling

        max_size = sqrt(LEVEL_WIDTH * LEVEL_WIDTH + LEVEL_HEIGHT * LEVEL_HEIGHT)

        # Normalize the color value in between 0-255
        # This then needs to be "flipped" ex 240 would be 15
        val = 255 - normalize(distance_to_wall, 0, max_size, 0, 255)

        cast_list.append([ceiling, floor, i, val, target_wall])

    draw_screen(s, cast_list)
    draw_sprites(s, cast_list)
    draw_minimap(s, g, cast_list)


def draw_screen(s, c):
    # Draw each cast as a vertical line to be matched up with the next cast for
    # smoooooth walls

    # Draw the sky
    pg.draw.rect(s, (135, 206, 235),
                 (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT / 2))

    # Draw the floor so its prettier
    pg.draw.rect(s, (0, 64, 0),
                 (0, SCREEN_HEIGHT / 2, SCREEN_WIDTH, SCREEN_HEIGHT / 2))

    for i in range(len(c)):
        try:
            if i + 1 >= len(c):
                continue  # finish the wall

            if c[i][0] is 0 and c[i][1] is 0:
                continue  # I'm super good at coding and this leaves the problem of not drawing the last line

            # The X offsets of the current vertical line and the subsequent line
            x1 = c[i][2]
            x2 = c[i + 1][2]
            val = c[i][3]
            color = (val, val, val)

            coordinates = [(x1, c[i][0]),  # Ceiling of current cell
                           (x2, c[i + 1][0]),  # Ceiling of next cell
                           (x2, c[i + 1][1]),  # Floor of next cell
                           (x1, c[i][1])]  # Floor of current cell
            pg.draw.polygon(s, color, coordinates, 0)
        except IndexError as e:  # e here incase I want to use it later,
            logger.log("you done it now boy")


def draw_sprites(s, c):
    """
    For sprite drawing we'll need to build a "Z buffer" ordered by distance to the player, drawing each item in the list
    in reverse order (farthest thing first, closest thing last)
    :param s: surface to draw things to
    :param c: cast list, do I really need this????
    :return: nothing
    """
    pass


def draw_minimap(s, g, c):
    """
    DEBUG TOOL
    :param s:
    :param g:
    :param c:
    :return:
    """

    pg.draw.rect(s, pg.Color("Black"),
                 (SCREEN_WIDTH - (LEVEL_WIDTH * LEVEL_CELL_SPACING),
                  0,
                  LEVEL_WIDTH * LEVEL_CELL_SPACING,
                  LEVEL_HEIGHT * LEVEL_CELL_SPACING))

    # Translate the current player's position to the mini map structure
    player_pos = (int(SCREEN_WIDTH - (g.player.pos.x * LEVEL_CELL_SPACING)),
                  int(g.player.pos.y * LEVEL_CELL_SPACING))

    # Draw the player fov
    player_right_aim = (player_pos[0] - 20 * sin(g.player.angle + g.player.fov / 2),
                        player_pos[1] + 20 * cos(g.player.angle + g.player.fov / 2))
    player_left_aim = (player_pos[0] - 20 * sin(g.player.angle - g.player.fov / 2),
                       player_pos[1] + 20 * cos(g.player.angle - g.player.fov / 2))
    pg.draw.line(s, pg.Color("Red"), player_pos, player_left_aim)
    pg.draw.line(s, pg.Color("Red"), player_pos, player_right_aim)

    # Player
    pg.draw.circle(s, pg.Color("red"), player_pos, 1)
    for wall in g.level.walls:
        start = (int(SCREEN_WIDTH - (wall.p1.x * LEVEL_CELL_SPACING)),
                 int(wall.p1.y * LEVEL_CELL_SPACING))
        end = (int(SCREEN_WIDTH - (wall.p2.x * LEVEL_CELL_SPACING)),
               int(wall.p2.y * LEVEL_CELL_SPACING))
        pg.draw.line(s, pg.Color("Green"), start, end)
    for cast in c:
        try:
            ls = cast[4].p1
            le = cast[4].p2
            ls = (int(SCREEN_WIDTH - (ls.x * LEVEL_CELL_SPACING)),
                  int(ls.y * LEVEL_CELL_SPACING))
            le = (int(SCREEN_WIDTH - (le.x * LEVEL_CELL_SPACING)),
                  int(le.y * LEVEL_CELL_SPACING))
            pg.draw.line(s, pg.Color("Red"), ls, le)
        except IndexError:
            logger.log("index error")
        except TypeError as e:
            logger.log("Type error")


"""
The following Line and Point classes are tools I used to help make figure out this code easier, does it need to be here?
It probably overly complicates things but it also makes it easier to work with in my noggin
"""


def distance_to_point(a, b):
    """
    A simple point to point distance measure tool
    :param a: x, y coords of point a
    :param b: x, y coords of point a
    :return: float: distance between a and b
    """
    return sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2)


def is_on_line(p, l):
    """
    Checks if a point is on a line
    :param p: Point to check of type Point
    :param l: Line to be evaluated of type Line
    :return: bool, True if the point is on the line, else false
    """
    # Create local version of this function for shorter code allowing it to be read
    # on lower res screens easier
    d = distance_to_point
    if d(p, l.p1) + d(p, l.p2) == d(*l):
        return True
    return False


def line_intersection(l1, l2):
    """
    Takes two line objects and checks if they intersect, if they do return the x, y coordinate of the intersection
    else return False

    Using the following resource I was able to build a faster implementation of this than using the
    shapely library which was far too slow for these purposes (This is better but possibly not the final solution)
    http://paulbourke.net/geometry/pointlineplane/
    :param l1: A Line object
    :param l2: A line object
    :return: x, y or False
    """
    d = (l2.p2.y - l2.p1.y) * (l1.p2.x - l1.p1.x)\
        - \
        (l2.p2.x - l2.p1.x) * (l1.p2.y - l1.p1.y)
    if d == 0:
        return False

    a = (l2.p2.x - l2.p1.x) * (l1.p1.y - l2.p1.y)\
        - \
        (l2.p2.y - l2.p1.y) * (l1.p1.x - l2.p1.x)
    b = (l1.p2.x - l1.p1.x) * (l1.p1.y - l2.p1.y)\
        - \
        (l1.p2.y - l1.p1.y) * (l1.p1.x - l2.p1.x)

    ra = a / d
    rb = b / d

    if 0 <= ra <= 1 and 0 <= rb <= 1:
        x = l1.p1.x + (ra * (l1.p2.x - l1.p1.x))
        y = l1.p1.y + (ra * (l1.p2.y - l1.p1.y))
        return x, y
    else:
        return False


def normalize(val, old_min, old_max, new_min, new_max):
    old_range = old_max - old_min
    new_range = new_max - new_min
    return ((val - old_min) * new_range) / old_range + new_min

