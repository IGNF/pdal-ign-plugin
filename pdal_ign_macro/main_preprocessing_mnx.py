import argparse
import tempfile
from pathlib import Path

from pdaltools.add_points_in_pointcloud import add_points_from_geometry_to_las

from pdal_ign_macro import mark_points_to_use_for_digital_models_with_new_dimension


def parse_args():
    parser = argparse.ArgumentParser(
        "Preprocessing MNX: add virtual points and mark points to use for DTM/DSM"
    )
    parser.add_argument("--input_las", "-i", type=str, required=True, help="Input las file")
    parser.add_argument(
        "--output_las", "-o", type=str, required=True, help="Output cloud las file"
    )
    # Arguments related to adding virtual points
    parser.add_argument(
        "--input_geometry",
        "-ig",
        type=str,
        required=False,
        help="Input GeoJSON/shp file containing lines or points",
    )
    parser.add_argument(
        "--virtual_points_classes",
        "-c",
        type=int,
        default=66,
        help="classification value to assign to the added virtual points",
    )
    parser.add_argument(
        "--spacing",
        type=float,
        default=0.25,
        help="spacing between generated points in meters (if geojson contains lines) (default. 25 cm)",
    )
    parser.add_argument(
        "--altitude_column",
        "-z",
        type=str,
        required=False,
        default=None,
        help="altitude column name from input geometry (use point.z if altitude_column is not set)",
    )
    # Arguments elated to marking points
    parser.add_argument(
        "--dsm_dimension",
        type=str,
        required=False,
        default="dsm_marker",
        help="Dimension name for the output DSM marker",
    )
    parser.add_argument(
        "--dtm_dimension",
        type=str,
        required=False,
        default="dtm_marker",
        help="Dimension name for the output DTM marker",
    )
    parser.add_argument(
        "--output_dsm", "-s", type=str, required=False, default="", help="Output dsm tiff file"
    )
    parser.add_argument(
        "--output_dtm", "-t", type=str, required=False, default="", help="Output dtm tiff file"
    )
    parser.add_argument(
        "--keep_temporary_dims",
        "-k",
        action="store_true",
        help="If set, do not delete temporary dimensions",
    )
    # Arguments related to pointcloud geometry
    parser.add_argument(
        "--skip_buffer",
        action="store_true",
        help="If set, skip adding a buffer from the neighbor tiles based on their name",
    )
    parser.add_argument(
        "--buffer_width",
        type=float,
        default=25,
        help="width of the border to add to the tile (in meters)",
    )
    parser.add_argument(
        "--spatial_ref",
        type=str,
        required=True,
        help="spatial reference for the writer",
    )
    parser.add_argument(
        "--tile_width",
        type=int,
        default=1000,
        help="width of tiles in meters (required when running with a buffer)",
    )
    parser.add_argument(
        "--tile_coord_scale",
        type=int,
        default=1000,
        help="scale used in the filename to describe coordinates in meters (required when running with a buffer)",
    )

    return parser.parse_args()


def preprocess_mnx(
    input_las: str,
    input_geometry: str,
    spacing: float,
    altitude_column: str,
    output_las: str,
    dsm_dimension: str,
    dtm_dimension: str,
    output_dsm: str,
    output_dtm: str,
    keep_temporary_dims: bool,
    skip_buffer: bool,
    buffer_width: float,
    spatial_ref: str,
    virtual_points_classes: int,
    tile_width: int,
    tile_coord_scale: int,
):
    """Launch preprocessing before calculating MNX
    Args:
        input_las (str): Path to the LIDAR `.las/.laz` file.
        input_geometry (str): Path to the input GeoJSON file with 3D points (if None or "", only points marking is enabled)
        spacing (float): spacing between points generated along the geometry if it  contains lines. in meters (default. 25 cm)
        altitude_column (str): altitude column name from input geometry (use point.z if altitude_column is empty)
        output_las (str): Path to save the updated LIDAR file (LAS/LAZ format).
        dsm_dimension (str): Dimension name for the output DSM marker
        dtm_dimension (str): Dimension name for the output DTM marker
        output_dsm (str): output dsm tiff file
        output_dtm (str): output dtm tiff file
        keep_temporary_dims (bool): If set, do not delete temporary dimensions
        skip_buffer (bool): If set, skip adding a buffer from the neighbor tiles based on their name
        buffer_width (float): width of the border to add to the tile (in meters)
        spatial_ref (str): CRS's value of the data in 'EPSG:XXXX' format
        virtual_points_classes (int):  The classification value to assign to those virtual points (default: 66).
        tile_width (int): Width of the tile in meters (default: 1000).
        tile_coord_scale (int): scale used in the filename to describe coordinates in meters (default: 1000).
    """

    # If no GeoJSON input is provided, we cannot add or mark points

    with tempfile.NamedTemporaryFile(
        prefix=Path(input_las).stem, suffix="_intermediate.laz", dir="."
    ) as tmp_las:
        if input_geometry:
            mark_points_input_path = tmp_las.name

            add_points_from_geometry_to_las(
                input_geometry,
                input_las,
                mark_points_input_path,
                virtual_points_classes,
                spatial_ref,
                tile_width,
                spacing,
                altitude_column,
            )
        else:
            print("No GeoJSON input provided. Skip adding points.")
            mark_points_input_path = input_las

        mark_points_to_use_for_digital_models_with_new_dimension.main(
            mark_points_input_path,
            output_las,
            dsm_dimension,
            dtm_dimension,
            output_dsm,
            output_dtm,
            keep_temporary_dims,
            skip_buffer=skip_buffer,
            buffer_width=buffer_width,
            spatial_ref=spatial_ref,
            tile_width=tile_width,
            tile_coord_scale=tile_coord_scale,
        )


if __name__ == "__main__":
    args = parse_args()
    preprocess_mnx(**vars(args))
