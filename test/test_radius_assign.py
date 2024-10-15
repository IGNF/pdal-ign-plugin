import json
import math
import random as rand
import tempfile
from test import utils

import numpy as np
import pdal
import pytest

pt_x = 1639825.1
pt_y = 1454924.6
pt_z = 7072.1
pt_ini = (pt_x, pt_y, pt_z, 1)

numeric_precision = 4
numeric_precision_z = 2
distance_radius = 1


def distance2d(pt1, pt2):
    return round(math.sqrt((pt1[0] - pt2[0]) ** 2 + (pt1[1] - pt2[1]) ** 2), numeric_precision)


def distance3d(pt1, pt2):
    return round(
        math.sqrt((pt1[0] - pt2[0]) ** 2 + (pt1[1] - pt2[1]) ** 2 + (pt1[2] - pt2[2]) ** 2),
        numeric_precision,
    )


def distanceZ(pt1, pt2):
    return round(pt1[2] - pt2[2], numeric_precision_z)


def run_filter(arrays_las, distance_radius, search_3d, limit_z_above=-1, limit_w_below=-1):

    filter = "filters.radius_assign"
    utils.pdal_has_plugin(filter)

    with tempfile.NamedTemporaryFile(suffix="_las_tmp.las") as las:
        pipeline = pdal.Writer.las(filename=las.name).pipeline(arrays_las)
        pipeline.execute()

        PIPELINE = [
            {"type": "readers.las", "filename": las.name},
            {"type": "filters.ferry", "dimensions": "=>SRC_DOMAIN"},
            {"type": "filters.ferry", "dimensions": "=>REF_DOMAIN"},
            {
                "type": "filters.assign",
                "value": [
                    "SRC_DOMAIN = 1 WHERE Classification==2",
                    "SRC_DOMAIN = 0 WHERE Classification!=2",
                    "REF_DOMAIN = 1 WHERE Classification==1",
                    "REF_DOMAIN = 0 WHERE Classification!=1",
                ],
            },
            {
                "type": filter,
                "radius": distance_radius,
                "src_domain": "SRC_DOMAIN",
                "reference_domain": "REF_DOMAIN",
                "output_dimension": "radius_search",
                "is3d": search_3d,
                "max2d_above": limit_z_above,
                "max2d_below": limit_w_below,
            },
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


def build_random_points_around_one_point(test_function, points=[]):

    dtype = [("X", "<f8"), ("Y", "<f8"), ("Z", "<f8"), ("Classification", "u1")]
    arrays_las = np.array([pt_ini], dtype=dtype)

    pt_limit = (pt_x + distance_radius, pt_y, pt_z, 2)
    arrays_pti = np.array([pt_limit], dtype=dtype)
    arrays_las = np.concatenate((arrays_las, arrays_pti), axis=0)
    nb_points_take = test_function(pt_limit)

    pt_limit = (pt_x + distance_radius + 1 / numeric_precision, pt_y, pt_z, 2)
    arrays_pti = np.array([pt_limit], dtype=dtype)
    arrays_las = np.concatenate((arrays_las, arrays_pti), axis=0)
    nb_points_take += test_function(pt_limit)

    arrays_pti = np.array([pt_ini], dtype=dtype)
    arrays_las = np.concatenate((arrays_las, arrays_pti), axis=0)
    nb_points_take = test_function(pt_limit)

    for pt in points:
        arrays_pt = np.array([pt], dtype=dtype)
        arrays_las = np.concatenate((arrays_las, arrays_pt), axis=0)
        nb_points_take += test_function(pt)

    nb_points = rand.randint(20, 50)
    for i in range(nb_points):
        # round at 1 to avoid precision numeric pb
        pti_x = pt_ini[0] + rand.uniform(-1.5, 1.5)
        pti_y = pt_ini[1] + rand.uniform(-1.5, 1.5)
        pti_z = pt_ini[2] + rand.uniform(-1.5, 1.5)
        pt_i = (pti_x, pti_y, pti_z, 2)

        # too much uncertainty between the digital precisions of pdal and the tests
        if abs(distance2d(pt_i, pt_ini) - distance_radius) < 1 / numeric_precision:
            continue
        if abs(distance3d(pt_i, pt_ini) - distance_radius) < 1 / numeric_precision:
            continue

        arrays_pti = np.array([pt_i], dtype=dtype)
        arrays_las = np.concatenate((arrays_las, arrays_pti), axis=0)

        nb_points_take += test_function(pt_i)

    return arrays_las, nb_points_take


def test_radius_assign_3d():

    def func_test(pt):
        distance_i = distance3d(pt_ini, pt)
        if distance_i < distance_radius:
            return 1
        return 0

    arrays_las, nb_points_take_3d = build_random_points_around_one_point(func_test)
    nb_pts_radius_3d = run_filter(arrays_las, distance_radius, True)
    assert nb_pts_radius_3d == nb_points_take_3d


def test_radius_assign_2d():

    def func_test(pt):
        distance_i = distance2d(pt_ini, pt)
        if distance_i < distance_radius:
            return 1
        return 0

    arrays_las, nb_points_take_2d = build_random_points_around_one_point(func_test)
    nb_pts_radius_2d = run_filter(arrays_las, distance_radius, False)
    assert nb_pts_radius_2d == nb_points_take_2d


def test_radius_assign_2d_cylinder_below():

    limit_z_below = 1.75
    limit_z_above = -1

    def func_test(pt):
        distance_i = distance2d(pt_ini, pt)
        distance_z = distanceZ(pt, pt_ini)
        if distance_i < distance_radius and distance_z < limit_z_below:
            return 1
        return 0

    arrays_las, nb_points_take_2d = build_random_points_around_one_point(func_test)

    nb_pts_radius_2d_cylinder = run_filter(
        arrays_las, distance_radius, False, limit_z_above, limit_z_below
    )
    assert nb_pts_radius_2d_cylinder == nb_points_take_2d


def test_radius_assign_2d_cylinder_above():

    limit_z_below = -1
    limit_z_above = 1.75

    points = []
    points.append((pt_x, pt_y, pt_z + limit_z_above, 2))

    def func_test(pt):
        distance_i = distance2d(pt_ini, pt)
        distance_z = distanceZ(pt_ini, pt)
        if distance_i < distance_radius and distance_z < limit_z_above:
            return 1
        return 0

    arrays_las, nb_points_take_2d = build_random_points_around_one_point(func_test, points)

    nb_pts_radius_2d_cylinder = run_filter(
        arrays_las, distance_radius, False, limit_z_above, limit_z_below
    )
    assert nb_pts_radius_2d_cylinder == nb_points_take_2d


def test_radius_assign_2d_cylinder_above_below_null():

    limit_z_below = 0
    limit_z_above = 0

    def func_test(pt):
        distance_i = distance2d(pt_ini, pt)
        distance_z = distanceZ(pt_ini, pt)
        if distance_i < distance_radius and distance_z == 0:
            return 1
        return 0

    arrays_las, nb_points_take_2d = build_random_points_around_one_point(func_test)

    nb_pts_radius_2d_cylinder = run_filter(
        arrays_las, distance_radius, False, limit_z_above, limit_z_below
    )
    assert nb_pts_radius_2d_cylinder == nb_points_take_2d


def test_radius_assign_2d_cylinder_above_null_bellow_all():

    limit_z_below = 0
    limit_z_above = -1

    def func_test(pt):
        distance_i = distance2d(pt_ini, pt)
        distance_z = distanceZ(pt, pt_ini)
        if distance_i < distance_radius and distance_z <= 0:
            return 1
        return 0

    arrays_las, nb_points_take_2d = build_random_points_around_one_point(func_test)

    nb_pts_radius_2d_cylinder = run_filter(
        arrays_las, distance_radius, False, limit_z_above, limit_z_below
    )
    assert nb_pts_radius_2d_cylinder == nb_points_take_2d


def test_radius_assign_2d_cylinder_above_bellow_all():

    limit_z_below = -1
    limit_z_above = -1

    def func_test(pt):
        distance_i = distance2d(pt_ini, pt)
        if distance_i < distance_radius:
            return 1
        return 0

    arrays_las, nb_points_take_2d = build_random_points_around_one_point(func_test)

    nb_pts_radius_2d_cylinder = run_filter(
        arrays_las, distance_radius, False, limit_z_above, limit_z_below
    )
    assert nb_pts_radius_2d_cylinder == nb_points_take_2d


@pytest.mark.parametrize("execution_number", range(10))
def test_radius_assign_2d_cylinder_above_and_bellow(execution_number):

    limit_z_below = rand.uniform(0, 2)
    limit_z_above = rand.uniform(0, 2)

    points = []
    points.append((pt_x, pt_y, pt_z + limit_z_above, 2))
    points.append((pt_x, pt_y, pt_z - limit_z_below, 2))

    def func_test(pt):
        distance_i = distance2d(pt_ini, pt)
        distance_z = distanceZ(pt, pt_ini)  # src - ref
        if distance_i < distance_radius:
            if distance_z <= 0 and (-distance_z) <= limit_z_above:  # src est sur ref
                return 1
            if distance_z >= 0 and distance_z <= limit_z_below:  # src est sous ref
                return 1
        return 0

    arrays_las, nb_points_take_2d = build_random_points_around_one_point(func_test, points)

    nb_pts_radius_2d_cylinder = run_filter(
        arrays_las, distance_radius, False, limit_z_above, limit_z_below
    )
    assert nb_pts_radius_2d_cylinder == nb_points_take_2d


@pytest.mark.parametrize(
    "limit_z_above, limit_z_below",
    [
        (-1, -1),  # no limit
        (-1, 1.75),  # limit below only
        (1.75, -1),  # limit above only
        (0, -1),  # take all points below only
        (-1, 0),  # take all points above only
        (-0.5, 0.5),
        (-0.5, 0.25),
        (-0.005, 0.005),  # other tests
    ],
)
def test_radius_assign_2d_cylinder(limit_z_above, limit_z_below):

    distance_radius = 1

    def func_test(pt):
        distance_i = distance2d(pt_ini, pt)
        if distance_i < distance_radius:
            distance_z = distanceZ(pt, pt_ini)  # src - ref
            if limit_z_above >= 0 and distance_z <= 0 and (-distance_z) > limit_z_above:
                return 0
            if limit_z_below >= 0 and distance_z >= 0 and distance_z > limit_z_below:
                return 0
            return 1
        else:
            return 0

    arrays_las, nb_points_take_2d = build_random_points_around_one_point(func_test)

    assert len(arrays_las) > 0

    nb_pts_radius_2d_cylinder = run_filter(
        arrays_las, distance_radius, False, limit_z_above, limit_z_below
    )

    assert nb_pts_radius_2d_cylinder == nb_points_take_2d
