import inspect
import tempfile

import numpy as np
import pdal

from pdal_ign_macro.mark_points_to_use_for_digital_models_with_new_dimension import (
    main,
    mark_points_to_use_for_digital_models_with_new_dimension,
    parse_args,
)


def test_mark_points_to_use_for_digital_models_with_new_dimension():
    ini_las = "test/data/4_6.las"
    dsm_dimension = "dsm_marker"
    dtm_dimension = "dtm_marker"
    with tempfile.NamedTemporaryFile(suffix="_mark_points_output.las") as las_output:
        mark_points_to_use_for_digital_models_with_new_dimension(
            ini_las, las_output.name, dsm_dimension, dtm_dimension, "", ""
        )
        pipeline = pdal.Pipeline()
        pipeline |= pdal.Reader.las(ini_las)
        input_dimensions = set(pipeline.quickinfo["readers.las"]["dimensions"].split(", "))
        pipeline = pdal.Pipeline()
        pipeline |= pdal.Reader.las(las_output.name)
        output_dimensions = set(pipeline.quickinfo["readers.las"]["dimensions"].split(", "))
        assert output_dimensions == input_dimensions.union([dsm_dimension, dtm_dimension])

        pipeline.execute()
        arr = pipeline.arrays[0]
        assert np.any(arr[dsm_dimension] == 1)
        assert np.any(arr[dtm_dimension] == 1)


def test_mark_points_to_use_for_digital_models_with_new_dimension_keep_dimensions():
    ini_las = "test/data/4_6.las"
    dsm_dimension = "dsm_marker"
    dtm_dimension = "dtm_marker"
    with tempfile.NamedTemporaryFile(suffix="_mark_points_output.las") as las_output:
        mark_points_to_use_for_digital_models_with_new_dimension(
            ini_las,
            las_output.name,
            dsm_dimension,
            dtm_dimension,
            "",
            "",
            keep_temporary_dimensions=True,
        )
        pipeline = pdal.Pipeline()
        pipeline |= pdal.Reader.las(las_output.name)
        output_dimensions = set(pipeline.quickinfo["readers.las"]["dimensions"].split(", "))
        assert dsm_dimension in output_dimensions
        assert dtm_dimension in output_dimensions

        assert all(
            [
                dim in output_dimensions
                for dim in ["PT_VEG_DSM", "PT_ON_BRIDGE", "PT_ON_BUILDING", "PT_ON_VEGET"]
            ]
        )

        pipeline.execute()
        arr = pipeline.arrays[0]
        assert np.any(arr[dsm_dimension] == 1)
        assert np.any(arr[dtm_dimension] == 1)


def test_main_no_buffer():
    ini_las = "test/data/4_6.las"
    dsm_dimension = "dsm_marker"
    dtm_dimension = "dtm_marker"
    with tempfile.NamedTemporaryFile(suffix="_mark_points_output.las") as las_output:
        main(
            ini_las,
            las_output.name,
            dsm_dimension,
            dtm_dimension,
            "",
            "",
            keep_temporary_dims=False,
            skip_buffer=True,
        )
        pipeline = pdal.Pipeline()
        pipeline |= pdal.Reader.las(las_output.name)
        output_dimensions = pipeline.quickinfo["readers.las"]["dimensions"].split(", ")
        assert dsm_dimension in output_dimensions
        assert dtm_dimension in output_dimensions

        pipeline.execute()
        arr = pipeline.arrays[0]
        assert np.any(arr[dsm_dimension] == 1)
        assert np.any(arr[dtm_dimension] == 1)


def test_main_with_buffer():
    ini_las = "test/data/buffer/test_data_77055_627755_LA93_IGN69.laz"
    dsm_dimension = "dsm_marker"
    dtm_dimension = "dtm_marker"
    with tempfile.NamedTemporaryFile(suffix="_mark_points_output.las") as las_output:
        main(
            ini_las,
            las_output.name,
            dsm_dimension,
            dtm_dimension,
            "",
            "",
            keep_temporary_dims=False,
            skip_buffer=False,
            buffer_width=10,
            tile_width=50,
            tile_coord_scale=10,
        )
        pipeline = pdal.Pipeline()
        pipeline |= pdal.Reader.las(las_output.name)
        output_dimensions = pipeline.quickinfo["readers.las"]["dimensions"].split(", ")
        assert dsm_dimension in output_dimensions
        assert dtm_dimension in output_dimensions

        pipeline.execute()
        arr = pipeline.arrays[0]
        assert np.any(arr[dsm_dimension] == 1)
        assert np.any(arr[dtm_dimension] == 1)


def test_parse_args():
    # sanity check for arguments parsing
    args = parse_args(
        ["--input_las", "test/data/4_6.las", "--output_las", "tmp/parse_args_out.las"]
    )
    parsed_args_keys = args.__dict__.keys()
    main_parameters = inspect.signature(main).parameters.keys()
    assert parsed_args_keys == main_parameters
