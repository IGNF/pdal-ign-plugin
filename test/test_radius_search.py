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

    nb_pts_radius_search = 0
    for pt in array:
        if pt["radius_search"] > 0:
            nb_pts_radius_search += 1

    return nb_pts_radius_search


def build_random_points_around_one_point(test_function):

    pt_x = 1639825.15
    pt_y = 1454924.63
    pt_z = 7072.17
    pt_ini = (pt_x, pt_y, pt_z, 1)

    dtype = [('X', '<f8'), ('Y', '<f8'), ('Z', '<f8'), ('Classification', 'u1')]
    arrays_las = np.array([pt_ini], dtype=dtype)

    nb_points = randint(20, 50)
    nb_points_take = 0
    for i in range(nb_points):
        pti_x = pt_ini[0] + rand.uniform(-1.5, 1.5)
        pti_y = pt_ini[1] + rand.uniform(-1.5, 1.5)

        # pdal write takes 2 numbers precision (scale_z=0.01 and offset_z=0 by default)
        pti_z = round(pt_ini[2] + rand.uniform(-1.5, 1.5), 2)
        pt_i = (pti_x, pti_y, pti_z, 2)

        arrays_pti = np.array([pt_i], dtype=dtype)
        arrays_las = np.concatenate((arrays_las, arrays_pti), axis=0)

        nb_points_take += test_function(pt_ini, pt_i)

    return arrays_las, nb_points_take


def test_radius_search_3d():

    distance_radius = 1

    def func_test(pt_ini, pt):
        distance_i = distance3d(pt_ini, pt)
        if distance_i < distance_radius:
            return 1
        return 0

    arrays_las, nb_points_take_3d = build_random_points_around_one_point(func_test)
    nb_pts_radius_3d = run_filter(arrays_las, distance_radius, True)
    assert nb_pts_radius_3d == nb_points_take_3d


def test_radius_search_2d():

    distance_radius = 1

    def func_test(pt_ini, pt):
        distance_i = distance2d(pt_ini, pt)
        if distance_i < distance_radius:
            return 1
        return 0

    arrays_las, nb_points_take_2d = build_random_points_around_one_point(func_test)
    nb_pts_radius_2d = run_filter(arrays_las, distance_radius, False)
    assert nb_pts_radius_2d == nb_points_take_2d


def test_radius_search_2d_cylinder():

    distance_radius = 1
    distance_cylinder = 0.25

    def func_test(pt_ini, pt):
        distance_i = distance2d(pt_ini, pt)
        if distance_i < distance_radius:
            if abs(pt_ini[2] - pt[2]) < distance_cylinder:
                return 1
        return 0

    arrays_las, nb_points_take_2d = build_random_points_around_one_point(func_test)
    nb_pts_radius_2d_cylinder = run_filter(arrays_las, distance_radius, False, distance_cylinder)
    assert nb_pts_radius_2d_cylinder == nb_points_take_2d