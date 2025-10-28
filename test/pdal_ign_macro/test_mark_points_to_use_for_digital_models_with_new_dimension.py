import inspect
import tempfile

import os
import numpy as np
import pdal
import pytest
import laspy

from pdal_ign_macro.mark_points_to_use_for_digital_models_with_new_dimension import (
    main,
    mark_points_to_use_for_digital_models_with_new_dimension,
    parse_args,
)


def test_mark_points_to_use_for_digital_models_with_new_dimension():
    ini_las = "test/data/4_6.las"
    dsm_dimension = "dsm_marker"
    dtm_dimension = "dtm_marker"
    with tempfile.NamedTemporaryFile(
        suffix="_mark_points_output.las", delete_on_close=False
    ) as las_output:
        mark_points_to_use_for_digital_models_with_new_dimension(
            ini_las, las_output.name, dsm_dimension, dtm_dimension, "", ""
        )
        pipeline_input = pdal.Reader.las(ini_las).pipeline()
        input_dimensions = set(pipeline_input.quickinfo["readers.las"]["dimensions"].split(", "))
        pipeline_output = pdal.Reader.las(las_output.name).pipeline()
        output_dimensions = set(pipeline_output.quickinfo["readers.las"]["dimensions"].split(", "))
        assert output_dimensions == input_dimensions.union([dsm_dimension, dtm_dimension])

        # pipeline.quickinfo done before need that we re create the pipeline
        pipeline_output = pdal.Reader.las(las_output.name).pipeline()
        pipeline_output.execute()
        arr = pipeline_output.arrays[0]
        assert np.any(arr[dsm_dimension] == 1)
        assert np.any(arr[dtm_dimension] == 1)


def test_mark_points_to_use_for_digital_models_with_new_dimension_keep_dimensions():
    ini_las = "test/data/4_6.las"
    dsm_dimension = "dsm_marker"
    dtm_dimension = "dtm_marker"
    with tempfile.NamedTemporaryFile(
        suffix="_mark_points_output.las", delete_on_close=False
    ) as las_output:
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
        # pipeline.quickinfo done before need that we re create the pipeline
        pipeline = pdal.Reader.las(las_output.name).pipeline()
        pipeline.execute()
        arr = pipeline.arrays[0]
        assert np.any(arr[dsm_dimension] == 1)
        assert np.any(arr[dtm_dimension] == 1)


def test_main_no_buffer():
    ini_las = "test/data/4_6.las"
    dsm_dimension = "dsm_marker"
    dtm_dimension = "dtm_marker"
    with tempfile.NamedTemporaryFile(
        suffix="_mark_points_output.las", delete_on_close=False
    ) as las_output:
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
    with tempfile.NamedTemporaryFile(
        suffix="_mark_points_output.las", delete_on_close=False
    ) as las_output:
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
        "68.laz",
    ],
)
def test_algo_mark_points_for_dm_with_reference(crop):
    ini_las = "test/data/mnx/input/" + crop
    dsm_dimension = "dsm_marker"
    dtm_dimension = "dtm_marker"
    with tempfile.NamedTemporaryFile(suffix="_after.las", delete_on_close=False) as las_output:

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

        # Check that all points with Classification == 68 have dtm_dimension == 1
        class_68_mask = arr_result["Classification"] == 68
        num_class_68 = np.sum(class_68_mask)
        if num_class_68 > 0:
            dtm_values = arr_result[dtm_dimension][class_68_mask]
            num_not_dtm = np.sum(dtm_values != 1)
            assert (
                num_not_dtm == 0
            ), f"Found {num_not_dtm} points with Classification == 68 but {dtm_dimension} != 1"


def test_reset_tags():
    ini_las = "test/data/4_6.las"
    dsm_dimension = "dsm_marker"
    dtm_dimension = "dtm_marker"

    tmp_files = []
    tmp_test_dir = "test/data/tmp_test_dir"
    if not os.path.exists(tmp_test_dir):
        os.makedirs(tmp_test_dir)

    # check that extra are not in initial file
    ini = laspy.read(ini_las, "r")
    assert dtm_dimension not in ini.point_format.dimension_names
    assert dsm_dimension not in ini.point_format.dimension_names

    las_step1 = tmp_test_dir + "/las_step1.las"
    tmp_files.append(las_step1)
    # run mark-points  
    main(
        ini_las,
        las_step1,
        dsm_dimension,
        dtm_dimension,
        "",
        "",
        skip_buffer=True,
    )

    # check count of points with dsm_marker==0 or dtm_marker==0
    pipeline = pdal.Pipeline() | pdal.Reader.las(filename=las_step1)
    pipeline |= pdal.Filter.expression(expression=f"{dsm_dimension}==0 || {dtm_dimension}==0")
    ini_count = pipeline.execute()
    assert ini_count == 14997

    print(f"ini_count = {ini_count}")

    # assign value=1 to all points for dsm_marker and dtm_marker
    pipeline = pdal.Pipeline() | pdal.Reader.las(filename=las_step1)
    pipeline |= pdal.Filter.assign(value=[f"{dsm_dimension}=1", f"{dtm_dimension}=1"])
    las_step2 = tmp_test_dir + "/las_step2.las"
    tmp_files.append(las_step2)
    pipeline |= pdal.Writer.las(filename=las_step2, extra_dims="all")
    pipeline.execute()
    # check count of points with dsm_marker==0 or dtm_marker==0, should be 0
    pipeline = pdal.Pipeline() | pdal.Reader.las(filename=las_step2)
    pipeline |= pdal.Filter.expression(expression=f"{dsm_dimension}==0 || {dtm_dimension}==0")
    after_assign_count = pipeline.execute()

    assert after_assign_count == 0

    las_step3 = tmp_test_dir + "/las_step3.las"
    tmp_files.append(las_step3)
    # run mark-points with reset_tags=True
    main(
        las_step2,
        las_step3,
        dsm_dimension,
        dtm_dimension,
        output_dsm="",
        output_dtm="",
        reset_tags=True,
        skip_buffer=True,
    )

    pipeline = pdal.Pipeline() | pdal.Reader.las(las_step3)
    pipeline |= pdal.Filter.expression(expression=f"{dtm_dimension}==0 || {dsm_dimension}==0")
    after_reset_count = pipeline.execute()
        
    # clean temp dir
    for file in tmp_files:
        os.remove(file)
    os.rmdir(tmp_test_dir)

    assert after_reset_count == ini_count # tags should have been reset, equal to initial count
