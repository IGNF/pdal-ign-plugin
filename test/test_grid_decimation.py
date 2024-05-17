import csv
import json
import math
import tempfile
from test import utils

import pdal
import pdaltools.las_info as li
import pytest

def run_filter(type):

    ini_las = "test/data/4_6.las"
    resolution = 10

    tmp_out_las = tempfile.NamedTemporaryFile(suffix=".las").name
    tmp_out_wkt = tempfile.NamedTemporaryFile(suffix=".wkt").name

    filter = "filters.grid_decimation"
    utils.pdal_has_plugin(filter)

    bounds = li.las_get_xy_bounds(ini_las)

    d_width = math.floor((bounds[0][1] - bounds[0][0]) / resolution) + 1
    d_height = math.floor((bounds[1][1] - bounds[1][0]) / resolution) + 1
    nb_dalle = d_width * d_height

    PIPELINE = [
        {"type": "readers.las", "filename": ini_las},
        {
            "type": filter,
            "resolution": resolution,
            "output_type": type,
            "output_name_attribut": "grid",
            "output_wkt": tmp_out_wkt,
        },
        {
            "type": "writers.las",
            "extra_dims": "all",
            "filename": tmp_out_las,
            "where": "grid==1",
        },
    ]

    pipeline = pdal.Pipeline(json.dumps(PIPELINE))

    # execute the pipeline
    pipeline.execute()
    arrays = pipeline.arrays
    array = arrays[0]

    nb_pts_grid = 0
    for pt in array:
        if pt["grid"] > 0:
            nb_pts_grid += 1

    assert nb_pts_grid == 3234
    assert nb_pts_grid <= nb_dalle

    data = []
    with open(tmp_out_wkt, "r") as f:
        reader = csv.reader(f, delimiter="\t")
        for i, line in enumerate(reader):
            data.append(line[0])

    assert len(data) == nb_dalle

    return nb_pts_grid

def test_grid_decimation_max():
    run_filter("max")

def test_grid_decimation_max():
    run_filter("min")


