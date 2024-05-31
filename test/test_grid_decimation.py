import csv
import json
import math
import re
import tempfile
from test import utils

import pdal
import pdaltools.las_info as li


def parse_geometry(geometry):
    regex = r"[0-9-\.]+"
    parsed_geom = re.findall(regex, geometry)
    parsed_geom = [float(i) for i in parsed_geom]
    return (
        max(parsed_geom[::2]),
        min(parsed_geom[::2]),
        max(parsed_geom[1::2]),
        min(parsed_geom[1::2]),
    )


def read_las_crop(las, line, type):

    tmp_out_las = tempfile.NamedTemporaryFile(suffix=".las").name

    PIPELINE = [
        {"type": "readers.las", "filename": las, "extra_dims": "grid=uint8"},
        {
            "type": "filters.crop",
            "polygon": line,
        },
        {
            "type": "writers.las",
            "extra_dims": "all",
            "filename": tmp_out_las,
        },
    ]

    pipeline = pdal.Pipeline(json.dumps(PIPELINE))

    # execute the pipeline
    pipeline.execute()
    arrays = pipeline.arrays
    array = arrays[0]

    max_x, min_x, max_y, min_y = parse_geometry(line)

    ZGrid = 0
    if type == "max":
        Z = -9999
    else:
        Z = 9999
    for pt in array:
        if type == "max" and pt["Z"] > Z:
            Z = pt["Z"]
        if type == "min" and pt["Z"] < Z:
            Z = pt["Z"]
        if pt["grid"] > 0:
            # if the point is exactly on the bbox at xmax or ymax, it's one of another cell
            if pt["X"] == max_x:
                continue
            if pt["Y"] == max_y:
                continue
            ZGrid = pt["Z"]

    assert ZGrid == Z


def run_filter(type):

    ini_las = "test/data/4_6.las"
    resolution = 10

    tmp_out_las = tempfile.NamedTemporaryFile(suffix=".las").name
    tmp_out_wkt = tempfile.NamedTemporaryFile(suffix=".wkt").name

    filter = "filters.grid_decimation_deprecated"
    utils.pdal_has_plugin(filter)

    bounds = li.las_get_xy_bounds(ini_las)

    d_width = math.ceil((bounds[0][1] - bounds[0][0]) / resolution)
    d_height = math.ceil((bounds[1][1] - bounds[1][0]) / resolution)
    nb_dalle = d_width * d_height

    PIPELINE = [
        {"type": "readers.las", "filename": ini_las},
        {
            "type": filter,
            "resolution": resolution,
            "output_type": type,
            "output_dimension": "grid",
            "output_wkt": tmp_out_wkt,
        },
        {
            "type": "writers.las",
            "extra_dims": "all",
            "filename": tmp_out_las,
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

    data = []
    with open(tmp_out_wkt, "r") as f:
        reader = csv.reader(f, delimiter="\t")
        for i, line in enumerate(reader):
            data.append(line[0])
            read_las_crop(tmp_out_las, line[0], type)

    assert len(data) == nb_dalle


def test_grid_decimation_max():
    run_filter("max")


def test_grid_decimation_min():
    run_filter("min")
