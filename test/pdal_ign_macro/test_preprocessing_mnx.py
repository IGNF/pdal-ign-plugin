import tempfile

import numpy as np
import pdal
import pytest

from pdal_ign_macro.main_preprocessing_mnx import preprocess_mnx


@pytest.mark.parametrize(
    "ini_las, ini_geojson, spacing, altitude_column, skip_buffer, nb_points_added",
    [
        (
            # File that does not have points with class 66 yet
            "test/data/buffer/test_data_77055_627760_LA93_IGN69.laz",
            "test/data/points_3d/Points_virtuels_77055_627760.geojson",
            0,
            "RecupZ",
            False,
            3,
        ),
        (
            "test/data/buffer/test_data_77055_627760_LA93_IGN69.laz",
            "",  # No geojson
            0,
            "",
            False,
            0,
        ),
        (
            # Geojson that don't have points inside the las tile area
            "test/data/buffer/test_data_77055_627755_LA93_IGN69.laz",
            "test/data/points_3d/Points_virtuels_77055_627760.geojson",
            0,
            "RecupZ",
            False,
            0,
        ),
        (
            # Filename that does not contain coordinates should work if skip_buffer=True
            "test/data/mnx/input/crop_1.laz",
            "test/data/points_3d/points_virtuels.geojson",
            0,
            "RecupZ",
            True,
            0,
        ),
        (
            # input geometry with 2d lines
            "test/data/buffer/test_data_77055_627760_LA93_IGN69.laz",
            "test/data/lines_3d/Points_virtuels_lines_2d_77055_627760.geojson",
            1,
            "RecupZ",
            False,
            53,
        ),
        (
            # input geometry with 3d lines
            "test/data/buffer/test_data_77055_627760_LA93_IGN69.laz",
            "test/data/lines_3d/Points_virtuels_lines_3d_77055_627760.geojson",
            1,
            "",
            False,
            53,
        ),
    ],
)
def test_preprocess_mnx(
    ini_las, ini_geojson, spacing, altitude_column, skip_buffer, nb_points_added
):
    dsm_dimension = "dsm_marker"
    dtm_dimension = "dtm_marker"

    with tempfile.NamedTemporaryFile(suffix="_preprocessed_output.laz") as las_output:

        preprocess_mnx(
            input_las=ini_las,
            input_geometry=ini_geojson,
            spacing=spacing,
            altitude_column=altitude_column,
            output_las=las_output.name,
            dsm_dimension=dsm_dimension,
            dtm_dimension=dtm_dimension,
            output_dsm="",
            output_dtm="",
            keep_temporary_dims=False,
            skip_buffer=skip_buffer,
            buffer_width=0,
            spatial_ref="EPSG:2154",
            virtual_points_classes=66,
            tile_width=50,
            tile_coord_scale=10,
        )

        pipeline_mtd = pdal.Reader.las(las_output.name).pipeline()
        metadata = pipeline_mtd.quickinfo["readers.las"]["dimensions"]
        assert dsm_dimension in metadata, "DSM marker dimension not found"
        assert dtm_dimension in metadata, "DTM marker dimension not found"

        pipeline_output = pdal.Reader.las(las_output.name).pipeline()
        pipeline_output.execute()
        arr = pipeline_output.arrays[0]

        classif_values, counts = np.unique(arr["Classification"], return_counts=True)
        count_66 = counts[classif_values == 66] if 66 in classif_values else 0
        assert (
            count_66 == nb_points_added
        ), f"Expected {nb_points_added} points added with class 66, got {count_66}"

        assert np.any(arr[dsm_dimension] == 1), "No points marked for DSM"
        assert np.any(arr[dtm_dimension] == 1), "No points marked for DTM"
        assert not np.all(arr["Intensity"] == 0), "Lost Intensity value"


@pytest.mark.parametrize(
    "ini_las, ini_geojson, skip_buffer, error_type",
    [
        (
            # Filename that does not contain coordinates should work if skip_buffer=True
            "test/data/mnx/input/crop_1.laz",
            "",  # No geojson
            False,
            ValueError,
        ),
        (
            # Geojson file is 2d lines, but no altitude_column is provided
            "test/data/buffer/test_data_77055_627760_LA93_IGN69.laz",
            "test/data/lines_3d/Points_virtuels_lines_2d_77055_627760.geojson",
            True,
            NotImplementedError,
        ),
    ],
)
def test_preprocess_mnx_fail(ini_las, ini_geojson, skip_buffer, error_type):
    dsm_dimension = "dsm_marker"
    dtm_dimension = "dtm_marker"

    with pytest.raises(error_type):
        with tempfile.NamedTemporaryFile(suffix="_preprocessed_output.laz") as las_output:
            preprocess_mnx(
                input_las=ini_las,
                input_geometry=ini_geojson,
                spacing=0,
                altitude_column="",
                output_las=las_output.name,
                dsm_dimension=dsm_dimension,
                dtm_dimension=dtm_dimension,
                output_dsm="",
                output_dtm="",
                keep_temporary_dims=False,
                skip_buffer=skip_buffer,
                buffer_width=0,
                spatial_ref="EPSG:2154",
                virtual_points_classes=66,
                tile_width=50,
                tile_coord_scale=10,
            )
