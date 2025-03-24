import json
import tempfile
from test import utils

import pdal


def test_classify_by_geo():

    filter = "filters.classify_by_geo"
    utils.pdal_has_plugin(filter)

    ini_las = "test/data/4_6.las"
    datasource = "test/data/4_6_crop.geojson"

    with tempfile.NamedTemporaryFile(suffix="_out.las") as out_las:

        PIPELINE = [
            {"type": "readers.las", "filename": ini_las},
            {
                "type": filter,
                "datasource": datasource,
                "new_class_value": 66,
            },
            {
                "type": "writers.las",
                "filename": out_las.name,
                "extra_dims": "all",
                "forward": "all",
                "minor_version": 4,
            },
        ]

        pipeline = pdal.Pipeline(json.dumps(PIPELINE))
        pipeline.execute()
        arrays = pipeline.arrays
        array = arrays[0]

        nb_pts_inside = 0
        for pt in array:
            if pt["Classification"] == 66:
                nb_pts_inside += 1

        assert nb_pts_inside > 0
