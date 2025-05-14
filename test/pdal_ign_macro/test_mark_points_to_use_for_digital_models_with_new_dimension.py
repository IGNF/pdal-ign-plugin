import inspect
import tempfile

import numpy as np
import pdal
import pytest

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
        pipeline_input = pdal.Reader.las(ini_las).pipeline()
        input_dimensions = set(pipeline_input.quickinfo["readers.las"]["dimensions"].split(", "))
        pipeline_output = pdal.Reader.las(las_output.name).pipeline()
        output_dimensions = set(pipeline_output.quickinfo["readers.las"]["dimensions"].split(", "))
        assert output_dimensions == input_dimensions.union([dsm_dimension, dtm_dimension])

        pipeline_output = pdal.Reader.las(las_output.name).pipeline()
        pipeline_output.execute()
        arr = pipeline_output.arrays[0]
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
        pipeline_mtd = pdal.Reader.las(las_output.name).pipeline()
        output_dimensions = set(pipeline_mtd.quickinfo["readers.las"]["dimensions"].split(", "))
        assert dsm_dimension in output_dimensions
        assert dtm_dimension in output_dimensions
        assert all(
            [
                dim in output_dimensions
                for dim in [
                    "PT_VEG_DSM",
                    "PT_UNDER_BRIDGE",
                    "PT_CLOSED_BUILDING",
                    "PT_UNDER_VEGET",
                ]
            ]
        )

        pipeline = pdal.Reader.las(las_output.name).pipeline()
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

        pipeline_mtd = pdal.Reader.las(filename=las_output.name).pipeline()
        metadata = pipeline_mtd.quickinfo["readers.las"]["dimensions"]
        assert dsm_dimension in metadata
        assert dtm_dimension in metadata

        pipeline = pdal.Reader.las(filename=las_output.name).pipeline()
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

        pipeline_mtd = pdal.Reader.las(las_output.name).pipeline()
        output_dimensions = pipeline_mtd.quickinfo["readers.las"]["dimensions"]
        assert dsm_dimension in output_dimensions
        assert dtm_dimension in output_dimensions

        pipeline_out = pdal.Reader.las(las_output.name).pipeline()
        pipeline_out.execute()
        arr = pipeline_out.arrays[0]
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


@pytest.mark.parametrize(
    "crop",
    [
        "crop_1.laz",
        # "crop_2.laz", ToDo : rebuild the reference for crop_2 which is false
        "crop_3.laz",
        "bat.laz",
        "pont.laz",
        "corse.laz",
    ],
)
def test_algo_mark_points_for_dm_with_reference(crop):
    ini_las = "test/data/mnx/input/" + crop
    dsm_dimension = "dsm_marker"
    dtm_dimension = "dtm_marker"
    with tempfile.NamedTemporaryFile(suffix="_after.las") as las_output:

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

        def sort_points(points):
            sorted_index = np.lexsort((points["Y"], points["X"], points["Z"], points["GpsTime"]))
            np.set_printoptions(precision=30)
            sorted_points = points[sorted_index]
            return sorted_points

        pipeline_calc = pdal.Pipeline() | pdal.Reader.las(filename=las_output.name)
        pipeline_calc.execute()
        arr_result = pipeline_calc.arrays[0]

        # read reference :
        ref_las = "test/data/mnx/reference/" + crop

        pipeline_ref = pdal.Pipeline() | pdal.Reader.las(filename=ref_las)
        pipeline_ref.execute()
        arr_reference = pipeline_ref.arrays[0]

        assert len(arr_result) == len(arr_reference)

        arr_result = sort_points(arr_result)
        arr_reference = sort_points(arr_reference)

        arr_result_dimensions = list(arr_result.dtype.fields.keys())
        arr_ref_dimensions = list(arr_reference.dtype.fields.keys())

        assert arr_result_dimensions == arr_ref_dimensions

        for dim in arr_result_dimensions:
            diff_mask = np.where(arr_result[dim] == arr_reference[dim], 0, 1)
            nb_pts_incorrect = np.count_nonzero(diff_mask)
            assert nb_pts_incorrect == 0
