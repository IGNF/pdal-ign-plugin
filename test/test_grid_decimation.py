import pytest
import json
import pdal
import os
import tempfile

from test import utils

def test_grid_decimation():

    tmp_out_las = tempfile.NamedTemporaryFile(suffix='.las').name

    filter = 'filters.grid_decimation'
    utils.pdal_has_plugin(filter)

    PIPELINE = [
        {
            "type":"readers.las",
            "filename":"test/data/4_6.las"
        },
        {
            "type":filter,
            "resolution":1,
            "output_type":"max",
            "output_name_attribut":"grid"
        },
        {
            "type":"writers.las",
            "extra_dims":"all",
            "filename":tmp_out_las
        }
    ]

    pipeline = pdal.Pipeline(json.dumps(PIPELINE))

    # execute the pipeline
    pipeline.execute()
    arrays = pipeline.arrays

    NbPtsGrid = 0
    for pt in arrays:
        if pt[grid] > 0:
            NbPtsGrid += 1

    assert nbThreadPts == 65067