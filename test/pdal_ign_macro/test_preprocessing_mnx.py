import os
import tempfile

import numpy as np
import pdal

from pdal_ign_macro.main_preprocessing_mnx import preprocess_mnx


def test_preprocess_mnx():
    # Test file paths
    ini_las = "test/data/buffer/test_data_77055_627755_LA93_IGN69.laz"
    ini_geojson = "test/data/points_3d/Points_virtuels_77055_627755.geojson"
    dsm_dimension = "dsm_marker"
    dtm_dimension = "dtm_marker"

    test_cases = [
        {"add_points": True, "mark_points": False},
        {"add_points": False, "mark_points": True},
        {"add_points": True, "mark_points": True},
    ]

    for case in test_cases:
        add_points = case["add_points"]
        mark_points = case["mark_points"]
        print(f"Testing with add_points={add_points}, mark_points={mark_points}")

        with tempfile.NamedTemporaryFile(suffix="_preprocessed_output.laz") as las_output:
            preprocess_mnx(
                input_las=ini_las,
                input_geojson=ini_geojson,
                output_las=las_output.name,
                dsm_dimension=dsm_dimension,
                dtm_dimension=dtm_dimension,
                output_dsm="",
                output_dtm="",
                keep_temporary_dims=False,
                skip_buffer=True,
                buffer_width=0,
                spatial_ref="EPSG:2154",
                virtual_points_classes=66,
                tile_width=50,
                tile_coord_scale=10,
                add_points=add_points,
                mark_points=mark_points,
            )

            pipeline_output = pdal.Pipeline()
            pipeline_output |= pdal.Reader.las(las_output.name)
            pipeline_output.execute()
            arr = pipeline_output.arrays[0]
            output_dimensions = set(
                pipeline_output.quickinfo["readers.las"]["dimensions"].split(", ")
            )

            if add_points:
                classes = np.unique(arr["Classification"])
                assert 66 in classes, "Virtual points with classification 66 were not added"
                print("Virtual points successfully added.")

            if mark_points:
                assert dsm_dimension in output_dimensions, "DSM marker dimension not found"
                assert dtm_dimension in output_dimensions, "DTM marker dimension not found"
                assert np.any(arr[dsm_dimension] == 1), "No points marked for DSM"
                assert np.any(arr[dtm_dimension] == 1), "No points marked for DTM"
                print("Marking points successfully added.")


def test_preprocess_mnx_with_output_files():
    # Test file paths
    ini_las = "test/data/buffer/test_data_77055_627755_LA93_IGN69.laz"
    ini_geojson = "test/data/points_3d/Points_virtuels_77055_627755.geojson"
    dsm_dimension = "dsm_marker"
    dtm_dimension = "dtm_marker"

    test_cases = [
        {"add_points": False, "mark_points": True},
        {"add_points": True, "mark_points": True},
    ]

    for case in test_cases:
        add_points = case["add_points"]
        mark_points = case["mark_points"]
        print(f"Testing with add_points={add_points}, mark_points={mark_points}")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_las = os.path.join(temp_dir, "output.las")
            output_dsm = os.path.join(temp_dir, "output_dsm.tiff")
            output_dtm = os.path.join(temp_dir, "output_dtm.tiff")

            # Execute preprocessing function with DSM/DTM generation
            preprocess_mnx(
                input_las=ini_las,
                input_geojson=ini_geojson,
                output_las=output_las,
                dsm_dimension=dsm_dimension,
                dtm_dimension=dtm_dimension,
                output_dsm=output_dsm,
                output_dtm=output_dtm,
                keep_temporary_dims=False,
                skip_buffer=True,
                buffer_width=0,
                spatial_ref="EPSG:2154",
                virtual_points_classes=66,
                tile_width=50,
                tile_coord_scale=10,
                add_points=add_points,
                mark_points=mark_points,
            )

            # Verify that files were created
            assert os.path.exists(output_las)
            assert os.path.exists(output_dsm)
            assert os.path.exists(output_dtm)

            # Check content of LAS file
            pipeline = pdal.Pipeline()
            pipeline |= pdal.Reader.las(output_las)
            pipeline.execute()
            arr = pipeline.arrays[0]

            assert dsm_dimension in arr.dtype.names
            assert dtm_dimension in arr.dtype.names
            assert np.any(arr[dsm_dimension] == 1)
            assert np.any(arr[dtm_dimension] == 1)
