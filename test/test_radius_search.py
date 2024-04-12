import json
import tempfile
from test import utils

from shapely.geometry import Point

from random import *
import numpy as np
import pdal
import random as rand
from math import *

import pytest

def test_radius_search():

    distance_radius = 1

    #shapely is 2d library
    def distance2d(pt1, pt2):
        return pt1.distance(pt2)
    def distance3d(pt1, pt2):
        return sqrt( (pt1.x-pt2.x)**2 + (pt1.y-pt2.y)**2 + (pt1.z-pt2.z)**2 )

    pt_x = 1639825.15
    pt_y = 1454924.63
    pt_z = 7072.17
    pt_ini = (pt_x, pt_y, pt_z, 1)
    pt1 = Point(pt_x, pt_y, pt_z)

    dtype = [('X', '<f8'), ('Y', '<f8'), ('Z', '<f8'), ('Classification', 'u1')]

    arrays_pts = np.array([pt_ini], dtype=dtype)

    nb_points = randint(10, 20)
    nb_points_take_2d = 0
    nb_points_take_3d = 0
    nb_points_take_2d_above_bellow = 0

    for i in range(nb_points):
        pti_x = pt_x + rand.uniform(-1.5, 1.5)
        pti_y = pt_y + rand.uniform(-1.5, 1.5)
        pti_z = round(pt_z + rand.uniform(-1.5, 1.5),2) #pdal only takes 2 numbers precision
        pt_i = (pti_x, pti_y, pti_z, 2)

        arrays_pti = np.array([pt_i], dtype=dtype)
        arrays_pts = np.concatenate((arrays_pts, arrays_pti), axis=0)

        pt_ig = Point(pti_x, pti_y, pti_z)
        distance_i_2d = distance2d(pt1, pt_ig)
        distance_i_3d = distance3d(pt1, pt_ig)

        if distance_i_2d < distance_radius:
            nb_points_take_2d += 1
            if abs(pti_z-pt_z)<0.5:
                nb_points_take_2d_above_bellow += 1
        if distance_i_3d < distance_radius:
            nb_points_take_3d += 1

    las_tmp = tempfile.NamedTemporaryFile(suffix="_las_tmp.las").name
    pipeline = pdal.Writer.las(filename=las_tmp).pipeline(arrays_pts)
    pipeline.execute()

    filter = "filters.radius_search"
    utils.pdal_has_plugin(filter)

    PIPELINE = [
        {"type": "readers.las", "filename": las_tmp},
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
            "search_2d_above": 0.5,
            "search_2d_bellow": 0.5,
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

    # execute the pipeline
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
    assert nb_pts_radius_2d_above_bellow == nb_points_take_2d_above_bellow