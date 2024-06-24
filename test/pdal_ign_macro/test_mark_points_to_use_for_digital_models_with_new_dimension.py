import tempfile

import numpy as np
import pdal

from pdal_ign_macro.mark_points_to_use_for_digital_models_with_new_dimension import (
    mark_points_to_use_for_digital_models_with_new_dimension,
)


def test_main():
    ini_las = "test/data/4_6.las"
    dsm_dimension = "dsm_marker"
    dtm_dimension = "dtm_marker"
    with tempfile.NamedTemporaryFile(suffix="_mark_points_output.las") as las_output:
        mark_points_to_use_for_digital_models_with_new_dimension(
            ini_las, las_output.name, dsm_dimension, dtm_dimension, "", ""
        )
        pipeline = pdal.Pipeline()
        pipeline |= pdal.Reader.las(las_output.name)
        assert dsm_dimension in pipeline.quickinfo["readers.las"]["dimensions"].split(", ")
        assert dtm_dimension in pipeline.quickinfo["readers.las"]["dimensions"].split(", ")

        pipeline.execute()
        arr = pipeline.arrays[0]
        assert np.any(arr[dsm_dimension] == 1)
        assert np.any(arr[dtm_dimension] == 1)
