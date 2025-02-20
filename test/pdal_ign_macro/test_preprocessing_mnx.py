import os
import tempfile

import numpy as np
import pdal

from pdal_ign_macro.main_preprocessing_mnx import preprocess_mnx


def test_preprocess_mnx():
    # Test file paths
    input_las = "test/data/4_6.las"
    input_geojson = "test/data/points_3d/points_virtuels.geojson"
    dsm_dimension = "dsm_marker"
    dtm_dimension = "dtm_marker"

    with tempfile.NamedTemporaryFile(suffix="_preprocessed_output.las") as las_output:
        # Execute the preprocessing function
        preprocess_mnx(
            input_las=input_las,
            input_geojson=input_geojson,
            output_las=las_output.name,
            dsm_dimension=dsm_dimension,
            dtm_dimension=dtm_dimension,
            output_dsm="",
            output_dtm="",
            keep_temporary_dims=True,
            skip_buffer=True,
            buffer_width=25.0,
            spatial_ref="EPSG:2154",
            virtual_points_classes=66,
            tile_width=1000,
            tile_coord_scale=1000,
        )

        # Check initial dimensions of input file
        pipeline_input = pdal.Pipeline()
        pipeline_input |= pdal.Reader.las(input_las)
        input_dimensions = set(pipeline_input.quickinfo["readers.las"]["dimensions"].split(", "))

        # Check dimensions of output file
        pipeline_output = pdal.Pipeline()
        pipeline_output |= pdal.Reader.las(las_output.name)
        output_dimensions = set(pipeline_output.quickinfo["readers.las"]["dimensions"].split(", "))

        # Verify that new dimensions have been added
        assert output_dimensions.issuperset(input_dimensions)
        assert dsm_dimension in output_dimensions
        assert dtm_dimension in output_dimensions

        # Execute pipeline to access data
        pipeline_output.execute()
        arr = pipeline_output.arrays[0]

        # Check for points marked for DSM and DTM
        assert np.any(arr[dsm_dimension] == 1)
        assert np.any(arr[dtm_dimension] == 1)

        # Verify presence of virtual points
        classes = np.unique(arr["Classification"])
        assert 66 in classes, "Virtual points with classification 66 were not added"


def test_preprocess_mnx_with_output_files():
    # Test file paths
    input_las = "test/data/4_6.las"
    input_geojson = "test/data/points_3d/points_virtuels.geojson"
    dsm_dimension = "dsm_marker"
    dtm_dimension = "dtm_marker"

    with tempfile.TemporaryDirectory() as temp_dir:
        output_las = os.path.join(temp_dir, "output.las")
        output_dsm = os.path.join(temp_dir, "output_dsm.tiff")
        output_dtm = os.path.join(temp_dir, "output_dtm.tiff")

        # Execute preprocessing function with DSM/DTM generation
        preprocess_mnx(
            input_las=input_las,
            input_geojson=input_geojson,
            output_las=output_las,
            dsm_dimension=dsm_dimension,
            dtm_dimension=dtm_dimension,
            output_dsm=output_dsm,
            output_dtm=output_dtm,
            keep_temporary_dims=True,
            skip_buffer=True,
            buffer_width=25.0,
            spatial_ref="EPSG:2154",
            virtual_points_classes=66,
            tile_width=1000,
            tile_coord_scale=1000,
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
