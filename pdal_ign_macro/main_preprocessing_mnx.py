import argparse
import tempfile

from pdaltools.add_points_in_pointcloud import add_points_in_las

from pdal_ign_macro import mark_points_to_use_for_digital_models_with_new_dimension


def parse_args():
    parser = argparse.ArgumentParser("TODO")
    parser.add_argument("--input_las", "-i", type=str, required=True, help="Input las file")
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
        default="EPSG:2154",
        help="spatial reference for the writer (required when running with a buffer)",
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
    parser.add_argument("ARGUMENTS ADD POINTS")


def preprocess_mnx(input_las, output_las):
    with tempfile.NamedTemporaryFile(suffix="_intermediate.las", dir=".") as tmp_las:
        add_points_in_las(input_las, tmp_las.name, "other args")
        mark_points_to_use_for_digital_models_with_new_dimension.main(
            tmp_las.name, output_las, "other args"
        )


if __name__ == "__main__":
    args = parse_args()
    preprocess_mnx(**vars(args))
