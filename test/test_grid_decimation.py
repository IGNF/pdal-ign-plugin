import csv
import json
import math
import tempfile
from test import utils

import numpy as np
import pdal
import pdaltools.las_info as li
import pytest


def contains(bounds, x, y):
    # to be coherent with the grid decimation algorithm
    return bounds[0] <= x and x < bounds[1] and bounds[2] <= y and y < bounds[3]


def run_filter(output_type, resolution):

    ini_las = "test/data/4_6.las"

    tmp_out_wkt = tempfile.NamedTemporaryFile(suffix=f"_{resolution}.wkt").name

    filter_name = "filters.grid_decimation_deprecated"
    utils.pdal_has_plugin(filter_name)

    bounds = li.las_get_xy_bounds(ini_las)

    d_width = math.floor((bounds[0][1] - bounds[0][0]) / resolution) + 1
    d_height = math.floor((bounds[1][1] - bounds[1][0]) / resolution) + 1
    nb_dalle = d_width * d_height

    PIPELINE = [
        {"type": "readers.las", "filename": ini_las},
        {
            "type": filter_name,
            "resolution": resolution,
            "output_type": output_type,
            "output_dimension": "grid",
            "output_wkt": tmp_out_wkt,
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

    assert nb_pts_grid == nb_dalle

    for lig in range(d_height):
        for col in range(d_width):

            cell = [
                bounds[0][0] + col * resolution,
                bounds[0][0] + (col + 1) * resolution,
                bounds[1][0] + lig * resolution,
                bounds[1][0] + (lig + 1) * resolution,
            ]

            nbThreadPtsCrop = 0
            ZRef = 0
            ZRefGrid = 0

            for pt in array:
                x = pt["X"]
                y = pt["Y"]
                if not contains(cell, x, y):
                    continue

                z = pt["Z"]
                if output_type == "max":
                    if ZRef == 0 or z > ZRef:
                        ZRef = z
                elif output_type == "min":
                    if ZRef == 0 or z < ZRef:
                        ZRef = z

                if pt["grid"] > 0:
                    nbThreadPtsCrop += 1
                    ZRefGrid = z

            assert nbThreadPtsCrop == 1
            assert ZRef == ZRefGrid

    data = []
    with open(tmp_out_wkt, "r") as f:
        reader = csv.reader(f, delimiter="\t")
        for i, line in enumerate(reader):
            data.append(line[0])

    assert len(data) == nb_dalle


@pytest.mark.parametrize(
    "resolution",
    [(10.1), (10.0), (9.8)],
)
def test_grid_decimation_max(resolution):
    run_filter("max", resolution)


@pytest.mark.parametrize(
    "resolution",
    [(10.3), (10.0), (9.9)],
)
def test_grid_decimation_min(resolution):
    run_filter("min", resolution)


def test_grid_decimation_empty():
    ini_las = "test/data/4_6.las"
    with tempfile.NamedTemporaryFile(suffix="_empty.wkt") as tmp_out_wkt:
        pipeline = pdal.Pipeline() | pdal.Reader.las(filename=ini_las)
        pipeline |= pdal.Filter.grid_decimation_deprecated(
            resolution=10,
            output_type="min",
            output_dimension="grid",
            output_wkt=tmp_out_wkt.name,
            where="Classification==123",  # should create an empty result
        )
        pipeline.execute()

        with open(tmp_out_wkt.name, "r") as f:
            reader = csv.reader(f, delimiter="\t")
            lines = [line for line in reader]
            assert len(lines) == 0

        assert np.all(pipeline.arrays[0]["grid"] == 0)
