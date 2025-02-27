import tempfile

import numpy as np
import pdal
import pytest

from pdal_ign_macro.main_preprocessing_mnx import preprocess_mnx


@pytest.mark.parametrize(
    "ini_las, ini_geojson, skip_buffer, nb_points_added",
    [
        (
            # File that does not have points with class 66 yet
            "test/data/buffer/test_data_77055_627760_LA93_IGN69.laz",
            "test/data/points_3d/Points_virtuels_77055_627760.geojson",
            False,
            3,
        ),
        (
            "test/data/buffer/test_data_77055_627760_LA93_IGN69.laz",
            "",  # No geojson
            False,
            0,
        ),
        (
            # Geojson that don't have points inside the las tile area
            "test/data/buffer/test_data_77055_627755_LA93_IGN69.laz",
            "test/data/points_3d/Points_virtuels_77055_627760.geojson",
            False,
            0,
        ),
        (
            # Filename that does not contain coordinates should work if skip_buffer=True
            "test/data/mnx/input/crop_1.laz",
            "",  # No geojson
            True,
            0,
        ),
    ],
)
def test_preprocess_mnx(ini_las, ini_geojson, skip_buffer, nb_points_added):
    dsm_dimension = "dsm_marker"
    dtm_dimension = "dtm_marker"

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
            skip_buffer=skip_buffer,
            buffer_width=0,
            spatial_ref="EPSG:2154",
            virtual_points_classes=66,
            tile_width=50,
            tile_coord_scale=10,
        )

        pipeline_output = pdal.Pipeline()
        pipeline_output |= pdal.Reader.las(las_output.name)
        pipeline_output.execute()
        arr = pipeline_output.arrays[0]

        classif_values, counts = np.unique(arr["Classification"], return_counts=True)
        count_66 = counts[classif_values == 66] if 66 in classif_values else 0
        assert (
            count_66 == nb_points_added
        ), f"Expected {nb_points_added} points added with class 66, got {count_66}"

        output_dimensions = set(pipeline_output.quickinfo["readers.las"]["dimensions"].split(", "))
        assert dsm_dimension in output_dimensions, "DSM marker dimension not found"
        assert dtm_dimension in output_dimensions, "DTM marker dimension not found"
        assert np.any(arr[dsm_dimension] == 1), "No points marked for DSM"
        assert np.any(arr[dtm_dimension] == 1), "No points marked for DTM"


@pytest.mark.parametrize(
    "ini_las, ini_geojson, skip_buffer",
    [
        (
            # Filename that does not contain coordinates should work if skip_buffer=True
            "test/data/mnx/input/crop_1.laz",
            "",  # No geojson
            False,
        ),
    ],
)
def test_preprocess_mnx_fail(ini_las, ini_geojson, skip_buffer):
    dsm_dimension = "dsm_marker"
    dtm_dimension = "dtm_marker"

    with pytest.raises(ValueError):
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
                skip_buffer=skip_buffer,
                buffer_width=0,
                spatial_ref="EPSG:2154",
                virtual_points_classes=66,
                tile_width=50,
                tile_coord_scale=10,
            )
