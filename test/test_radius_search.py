import json
import tempfile
from test import utils

from random import *
import numpy as np
import pdal
import random as rand
from math import *

import pytest

def test_radius_search():

    filter = "filters.radius_search"
    utils.pdal_has_plugin(filter)

    distance_radius = 1
    distance_cylinder = 0.5

    def distance2d(pt1, pt2):
        return sqrt( (pt1[0]-pt2[0])**2 + (pt1[1]-pt2[1])**2 )
    def distance3d(pt1, pt2):
        return sqrt( (pt1[0]-pt2[0])**2 + (pt1[1]-pt2[1])**2 + (pt1[2]-pt2[2])**2 )

    pt_x = 1639825.15
    pt_y = 1454924.63
    pt_z = 7072.17
    pt_ini = (pt_x, pt_y, pt_z, 1)

    dtype = [('X', '<f8'), ('Y', '<f8'), ('Z', '<f8'), ('Classification', 'u1')]

    arrays_pts = np.array([pt_ini], dtype=dtype)

    nb_points = randint(10, 20)
    nb_points_take_2d = 0
    nb_points_take_3d = 0
    nb_points_take_2d_above_below = 0

    for i in range(nb_points):
        pti_x = pt_x + rand.uniform(-1.5, 1.5)
        pti_y = pt_y + rand.uniform(-1.5, 1.5)

        # pdal write takes 2 numbers precision (scale_z=0.01 and offset_z=0 by default)
        pti_z = round(pt_z + rand.uniform(-1.5, 1.5), 2)
        pt_i = (pti_x, pti_y, pti_z, 2)

        arrays_pti = np.array([pt_i], dtype=dtype)
        arrays_pts = np.concatenate((arrays_pts, arrays_pti), axis=0)

        pt_ig = (pti_x, pti_y, pti_z)
        distance_i_2d = distance2d(pt_ini, pt_ig)
        distance_i_3d = distance3d(pt_ini, pt_ig)

        if distance_i_2d < distance_radius:
            nb_points_take_2d += 1
            if abs(pti_z-pt_z) < distance_cylinder:
                nb_points_take_2d_above_below += 1
        if distance_i_3d < distance_radius:
            nb_points_take_3d += 1

    with tempfile.NamedTemporaryFile(suffix="_las_tmp.las") as las:
        pipeline = pdal.Writer.las(filename=las.name).pipeline(arrays_pts)
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
                "radius": "1.",
                "src_domain": "SRS_DOMAIN",
                "reference_domain": "REF_DOMAIN",
                "output_name_attribute": "radius_2D",
                "search_3d":False,
            },
            {
                "type": filter,
                "radius": "1.",
                "src_domain": "SRS_DOMAIN",
                "reference_domain": "REF_DOMAIN",
                "output_name_attribute": "radius_2D_above_bellow",
                "search_3d": False,
                "search_2d_above": distance_cylinder,
                "search_2d_bellow": distance_cylinder,
            },
            {
                "type": filter,
                "radius": "1.",
                "src_domain": "SRS_DOMAIN",
                "reference_domain": "REF_DOMAIN",
                "output_name_attribute": "radius_3D",
                "search_3d": True
            }
        ]

        pipeline = pdal.Pipeline(json.dumps(PIPELINE))
        pipeline.execute()
        arrays = pipeline.arrays
        array = arrays[0]

    nb_pts_radius_2d = 0
    nb_pts_radius_3d = 0
    nb_pts_radius_2d_above_bellow = 0
    for pt in array:
        if pt["radius_2D_above_bellow"] > 0:
            nb_pts_radius_2d_above_bellow += 1
        if pt["radius_2D"] > 0:
            nb_pts_radius_2d += 1
        if pt["radius_3D"] > 0:
             nb_pts_radius_3d += 1

    assert nb_pts_radius_2d == nb_points_take_2d
    assert nb_pts_radius_3d == nb_points_take_3d
    assert nb_pts_radius_2d_above_bellow == nb_points_take_2d_above_below