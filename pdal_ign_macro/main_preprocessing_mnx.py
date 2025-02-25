import argparse
import os
import tempfile

from pdaltools.add_points_in_pointcloud import add_points_from_geojson_to_las

from pdal_ign_macro import mark_points_to_use_for_digital_models_with_new_dimension


def parse_args(argv=None):
    parser = argparse.ArgumentParser("Preprocessing MNX")
    parser.add_argument("--input_las", "-i", type=str, required=True, help="Input las file")
    parser.add_argument(
        "--input_geojson", "-ig", type=str, required=False, help="Input GeoJSON file"
    )
    parser.add_argument(
        "--output_las", "-o", type=str, required=True, help="Output cloud las file"
    )
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
        "--virtual_points_classes",
        "-c",
        type=int,
        default=66,
        help="classification value to assign to the added virtual points",
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
    parser.add_argument(
        "--add_points", action="store_true", help="Only run add_points_from_geojson_to_las"
    )
    parser.add_argument(
        "--mark_points",
        action="store_true",
        help="Only run mark_points_to_use_for_digital_models_with_new_dimension",
    )

    return parser.parse_args(argv)


def preprocess_mnx(
    input_las: str,
    input_geojson: str,
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
    add_points: bool,
    mark_points: bool,
):
    """Lauch preprocessing before calculating MNX
    Args:
        input_las (str): Path to the LIDAR `.las/.laz` file.
        input_geosjon (str): Path to the input GeoJSON file with 3D points.
        output_las (str): Path to save the updated LIDAR file (LAS/LAZ format).
        dsm_dimension (str): Dimension name for the output DSM marker
        dtm_dimension (str): Dimension name for the output DTM marker
        output_dsm (str): utput dsm tiff file
        output_dtm (str): utput dtm tiff file
        keep_temporary_dims (bool): If set, do not delete temporary dimensions
        skip_buffer (bool): If set, skip adding a buffer from the neighbor tiles based on their name
        buffer_width (float): width of the border to add to the tile (in meters)
        spatial_ref (str): CRS's value of the data in 'EPSG:XXXX' format
        virtual_points_classes (int):  The classification value to assign to those virtual points (default: 66).
        tile_width (int): Width of the tile in meters (default: 1000).
        tile_coord_scale (int): scale used in the filename to describe coordinates in meters (default: 1000).
        add_points (bool): If set, only run add_points_from_geojson_to_las.
        mark_points (bool): If set, only run mark_points_to_use_for_digital_models_with_new_dimension.
    """

    # If no GeoJSON input is provided, we cannot add or mark points
    if not input_geojson:
        print("No GeoJSON input provided. Skipping preprocessing.")
        return

    # Step 1: Define the intermediate LAS file path
    if mark_points:
        # Extract coordinates from input filename (assuming standard format)
        basename = os.path.basename(input_las)
        parts = basename.split("_")
        if len(parts) >= 5:
            prefix1, prefix2, coordx, coordy, suffix = parts[:5]  # Extract relevant parts
        else:
            raise ValueError(f"Invalid input LAS filename format: {basename}")
        # Construct the expected intermediate LAS filename
        expected_filename = f"{prefix1}_{prefix2}_{coordx}_{coordy}_intermediate.las"

        # Create a temporary file for intermediate processing
        with tempfile.NamedTemporaryFile(suffix="intermediate.las", dir=".") as tmp_las:
            intermediate_directory = os.path.dirname(tmp_las.name)
            # Rename the temporary file to match the expected format
            intermediate_filename = expected_filename
            intermediate_las = os.path.join(intermediate_directory, intermediate_filename)
    else:
        # If no marking is needed, use the final output as the intermediate file
        intermediate_las = output_las

    # Step 2: Add points from GeoJSON to LAS (if required)
    if add_points:
        add_points_from_geojson_to_las(
            input_geojson,
            input_las,
            intermediate_las,
            virtual_points_classes,
            spatial_ref,
            tile_width,
        )

    # Step 3: Mark points for digital models (if required)
    if mark_points:
        mark_points_to_use_for_digital_models_with_new_dimension.main(
            intermediate_las,
            output_las,
            dsm_dimension,
            dtm_dimension,
            output_dsm,
            output_dtm,
            keep_temporary_dims,
            skip_buffer,
            buffer_width,
            spatial_ref,
            tile_width,
            tile_coord_scale,
        )


if __name__ == "__main__":
    args = parse_args()
    preprocess_mnx(**vars(args))
