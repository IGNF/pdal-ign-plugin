import json
import tempfile
from test import utils

from random import *
import numpy as np
import pdal
import random as rand
from math import *

import pytest


def distance2d(pt1, pt2):
    return sqrt((pt1[0] - pt2[0]) ** 2 + (pt1[1] - pt2[1]) ** 2)


def distance3d(pt1, pt2):
    return sqrt((pt1[0] - pt2[0]) ** 2 + (pt1[1] - pt2[1]) ** 2 + (pt1[2] - pt2[2]) ** 2)

def build_random_points_arround_one_point(pt_ini):

    nb_points = randint(20, 50)
    arrays_pts = []
    for i in range(nb_points):
        pti_x = pt_ini[0] + rand.uniform(-1.5, 1.5)
        pti_y = pt_ini[1] + rand.uniform(-1.5, 1.5)

        # pdal write takes 2 numbers precision (scale_z=0.01 and offset_z=0 by default)
        pti_z = round(pt_ini[2] + rand.uniform(-1.5, 1.5), 2)
        pt_i = (pti_x, pti_y, pti_z, 2)
        arrays_pts.append(pt_i)

    return arrays_pts

def run_filter(arrays_las, distance_radius, search_3d, distance_cylinder=0. ):

    filter = "filters.radius_search"
    utils.pdal_has_plugin(filter)

    with tempfile.NamedTemporaryFile(suffix="_las_tmp.las") as las:
        pipeline = pdal.Writer.las(filename=las.name).pipeline(arrays_las)
        pipeline.execute()

        PIPELINE = [
            {"type": "readers.las", "filename": las.name},
            {
                "type": "filters.ferry",
                "dimensions": "=>SRS_DOMAIN"
            },
            {
                "type": "filters.ferry",
                "dimensions": "=>REF_DOMAIN"
            },
            {
                "type": "filters.assign",
                "value": [
                    "SRS_DOMAIN = 1 WHERE Classification==2",
                    "SRS_DOMAIN = 0 WHERE Classification!=2",
                    "REF_DOMAIN = 1 WHERE Classification==1",
                    "REF_DOMAIN = 0 WHERE Classification!=1",
                ],
            },
            {
                "type": filter,
                "radius": distance_radius,
                "src_domain": "SRS_DOMAIN",
                "reference_domain": "REF_DOMAIN",
                "output_name_attribute": "radius_search",
                "search_3d": search_3d,
                "search_2d_above": distance_cylinder,
                "search_2d_bellow": distance_cylinder,
            }
        ]

        pipeline = pdal.Pipeline(json.dumps(PIPELINE))
        pipeline.execute()
        arrays = pipeline.arrays
        array = arrays[0]

    return array

def test_radius_search_3d():

    distance_radius = 1
    nb_points_take_3d = 0

    pt_x = 1639825.15
    pt_y = 1454924.63
    pt_z = 7072.17
    pt_ini = (pt_x, pt_y, pt_z, 1)

    arrays_pts = build_random_points_arround_one_point(pt_ini)

    dtype = [('X', '<f8'), ('Y', '<f8'), ('Z', '<f8'), ('Classification', 'u1')]
    arrays_las = np.array([pt_ini], dtype=dtype)

    for pt in arrays_pts:
        arrays_pti = np.array([pt], dtype=dtype)
        arrays_las = np.concatenate((arrays_las, arrays_pti), axis=0)

        distance_i_3d = distance3d(pt_ini, pt)
        if distance_i_3d < distance_radius:
            nb_points_take_3d += 1

    array = run_filter(arrays_las, distance_radius, True)

    nb_pts_radius_3d = 0
    for pt in array:
        if pt["radius_search"] > 0:
            nb_pts_radius_3d += 1

    assert nb_pts_radius_3d == nb_points_take_3d


def test_radius_search_2d():

    distance_radius = 1
    nb_points_take_2d = 0

    pt_x = 1639825.15
    pt_y = 1454924.63
    pt_z = 7072.17
    pt_ini = (pt_x, pt_y, pt_z, 1)

    arrays_pts = build_random_points_arround_one_point(pt_ini)

    dtype = [('X', '<f8'), ('Y', '<f8'), ('Z', '<f8'), ('Classification', 'u1')]
    arrays_las = np.array([pt_ini], dtype=dtype)

    for pt in arrays_pts:
        arrays_pti = np.array([pt], dtype=dtype)
        arrays_las = np.concatenate((arrays_las, arrays_pti), axis=0)

        distance_i_2d = distance2d(pt_ini, pt)
        if distance_i_2d < distance_radius:
            nb_points_take_2d += 1

    array = run_filter(arrays_las, distance_radius, False)

    nb_pts_radius_2d = 0
    for pt in array:
        if pt["radius_search"] > 0:
            nb_pts_radius_2d += 1

    assert nb_pts_radius_2d == nb_points_take_2d


def test_radius_search_2d_cylinder():

    distance_radius = 1
    distance_cylinder = 0.25

    nb_points_take_2d = 0

    pt_x = 1639825.15
    pt_y = 1454924.63
    pt_z = 7072.17
    pt_ini = (pt_x, pt_y, pt_z, 1)

    arrays_pts = build_random_points_arround_one_point(pt_ini)

    dtype = [('X', '<f8'), ('Y', '<f8'), ('Z', '<f8'), ('Classification', 'u1')]
    arrays_las = np.array([pt_ini], dtype=dtype)

    for pt in arrays_pts:
        arrays_pti = np.array([pt], dtype=dtype)
        arrays_las = np.concatenate((arrays_las, arrays_pti), axis=0)

        distance_i_2d = distance2d(pt_ini, pt)
        if distance_i_2d < distance_radius:
            if abs(pt_ini[2] - pt[2]) < distance_cylinder:
                nb_points_take_2d += 1

    array = run_filter(arrays_las, distance_radius, False, distance_cylinder)

    nb_pts_radius_2d = 0
    for pt in array:
        if pt["radius_search"] > 0:
            nb_pts_radius_2d += 1

    assert nb_pts_radius_2d == nb_points_take_2d