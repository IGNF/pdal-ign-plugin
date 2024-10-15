import argparse
import shutil
import tempfile

import pdal
from pdaltools.las_add_buffer import run_on_buffered_las
from pdaltools.las_remove_dimensions import remove_dimensions_from_las

from pdal_ign_macro import macro

"""
This tool applies a pdal pipeline to select points for DSM and DTM calculation
It adds dimensions with positive values for the selected points
"""


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        "Tool to apply pdal pipelines to select points for DSM and DTM calculation"
        + "(add dimensions with positive values for the selected points)"
    )
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

    return parser.parse_args(argv)


def define_marking_pipeline(input_las, output_las, dsm_dimension, dtm_dimension):
    pipeline = pdal.Pipeline() | pdal.Reader.las(input_las)

    # 0 - ajout de dimensions temporaires et de sortie
    temporary_dimensions = [
        "PT_VEG_DSM",
        "PT_UNDER_BRIDGE",
        "PT_CLOSED_BUILDING",
        "PT_UNDER_VEGET",
        "PT_ON_SOL",
        "PT_ON_VIRT",
    ]
    added_dimensions = [dtm_dimension, dsm_dimension] + temporary_dimensions

    pipeline |= pdal.Filter.ferry(dimensions="=>" + ", =>".join(added_dimensions))

    ###################################################################################################################
    # 1 - Gestion de la végétation pour le calcul du DSM:
    ###################################################################################################################
    #       Recherche des points max de végétation (4,5) sur une grille régulière = PT_VEG_DSM=1,
    #       Prise en compte des points sol (2) proche de la végétation = PT_VEG_DSM=1
    #       Isolement des classes (hors sol) sous la végetation comme les bâtis, l'eau, les ponts et les divers-bâtis
    #       Prise en compte des points basse vegetation (3) proche de la végétation = PT_VEG_DSM=1
    #       Passage des premiers points "veget" PT_VEG_DSM=1 dans le taguage pour le MNS dsm_dimension=1

    # 1.1 Point veget max
    pipeline |= pdal.Filter.assign(
        value=["PT_VEG_DSM = 1 WHERE " + macro.build_condition("Classification", [4, 5])]
    )
    # 1.2 bouche trou : assigne les points sol à l'intérieur de la veget (4,5)
    pipeline = macro.add_radius_assign(
        pipeline,
        1,
        False,
        condition_src="Classification==2",
        condition_ref=macro.build_condition("Classification", [4, 5]),
        condition_out="PT_VEG_DSM=1",
    )
    pipeline = macro.add_radius_assign(
        pipeline,
        1,
        False,
        condition_src="PT_VEG_DSM==1 && Classification==2",
        condition_ref="Classification==2 && PT_VEG_DSM==0",
        condition_out="PT_VEG_DSM=0",
    )
    # 1.3 Isolement en PT_UNDER_VEGET=1 des éléments sous la végétation (hors sol)
    pipeline = macro.add_radius_assign(
        pipeline,
        1,
        False,
        condition_src=macro.build_condition("Classification", [6, 9, 17, 67]),
        condition_ref=macro.build_condition("Classification", [4, 5]),
        condition_out="PT_UNDER_VEGET=1",
        max2d_above=-1,
        max2d_below=0,
    )
    pipeline = macro.add_radius_assign(
        pipeline,
        1,
        False,
        condition_src="PT_UNDER_VEGET==1 && ( "
        + macro.build_condition("Classification", [6, 9, 17, 67])
        + " )",
        condition_ref="PT_UNDER_VEGET==0 && ( "
        + macro.build_condition("Classification", [6, 9, 17, 67])
        + " )",
        condition_out="PT_UNDER_VEGET=0",
        max2d_above=0.5,
        max2d_below=0.5,
    )
    # 1.4 selection des points de veget basse proche de la veget haute
    pipeline = macro.add_radius_assign(
        pipeline,
        1,
        False,
        condition_src="Classification==3",
        condition_ref="Classification==5",
        condition_out="PT_VEG_DSM=1",
    )
    # 1.5 Premiers points tagués pour le MNS
    # max des points de veget (PT_VEG_DSM==1) sur une grille régulière :
    # TODO: remplacer par GridDecimation une fois le correctif mergé dans PDAL
    pipeline |= pdal.Filter.grid_decimation_deprecated(
        resolution=0.75, output_dimension=dsm_dimension, output_type="max", where="PT_VEG_DSM==1"
    )
    ###################################################################################################################
    # 2 - Gestion de l'eau
    ###################################################################################################################
    #       L'eau sous la roche en dévers (typique Corse)
    #       Gestion de l'eau sur les masques hydro qui ne doivent pas se supperposer aux points virtuels 66

    # 2.1 L'eau sous la roche
    pipeline = macro.add_radius_assign(
        pipeline,
        1.25,
        False,
        condition_src="Classification==9",
        condition_ref="Classification==2",
        condition_out="PT_ON_SOL=1",
        max2d_above=-1,
        max2d_below=0,
    )
    pipeline = macro.add_radius_assign(
        pipeline,
        1,
        False,
        condition_src="PT_ON_SOL==1",
        condition_ref="PT_ON_SOL==0 && Classification==9",
        condition_out="PT_ON_SOL=0",
        max2d_above=0.5,
        max2d_below=0.5,
    )
    # 2.2 Gestion de l'eau sur les masques hydro
    pipeline = macro.add_radius_assign(
        pipeline,
        1,
        False,
        condition_src="Classification==9",
        condition_ref="Classification==66",
        condition_out="PT_ON_VIRT=1",
    )
    pipeline = macro.add_radius_assign(
        pipeline,
        1,
        False,
        condition_src="PT_ON_VIRT==1 && Classification==9",
        condition_ref="PT_ON_VIRT==0 && Classification==9",
        condition_out="PT_ON_VIRT=0",
    )
    ###################################################################################################################
    # 3 - sélection des premiers points pour MNT et MNS
    ###################################################################################################################
    #       Initialisation pour le MNT
    #       Initialisation pour le MNS

    # 3.1 Pour le MNT (le point sol max sur uen grille de 50cm)
    # TODO: remplacer par GridDecimation une fois le correctif mergé dans PDAL
    pipeline |= pdal.Filter.grid_decimation_deprecated(
        resolution=0.5,
        output_dimension=dtm_dimension,
        output_type="max",
        where="(Classification==2)",
    )
    # 3.2 Pour les MNS (Pour le moment: Les bâtis, ponts, veget)
    # TODO: remplacer par GridDecimation une fois le correctif mergé dans PDAL
    pipeline |= pdal.Filter.grid_decimation_deprecated(
        resolution=0.5,
        output_dimension=dsm_dimension,
        output_type="max",
        where="(PT_UNDER_VEGET==0 && ("
        + macro.build_condition("Classification", [6, 17, 67])
        + f") || {dsm_dimension}==1)",
    )
    # 3.3 Pour les points "eau" on prendra le point le plus bas de la grille de 50cm et qui ne sont ni sous la roche ni près de pts virtuels
    pipeline |= pdal.Filter.grid_decimation_deprecated(
        resolution=0.5,
        output_dimension=dtm_dimension,
        output_type="min",
        where="(PT_ON_SOL==0 && PT_ON_VIRT==0 && Classification==9)",
    )
    pipeline |= pdal.Filter.grid_decimation_deprecated(
        resolution=0.5,
        output_dimension=dsm_dimension,
        output_type="min",
        where="(PT_UNDER_VEGET==0 && PT_ON_SOL==0 && PT_ON_VIRT==0 && Classification==9)",
    )
    ###################################################################################################################
    # 4 - Gestion des points sol sous la veget,bâtis et ponts pour le MNS
    ###################################################################################################################
    #       On enlève les points sol sous la véget, le bati et les ponts du taguage pour les MNS
    #       Particularité de reprise des points sol au plus près des bâtiments

    # 4.1 Isolement des points sols sous la véget, le bati et les ponts
    pipeline = macro.add_radius_assign(
        pipeline,
        1.5,
        False,
        condition_src=f"{dtm_dimension}==1",
        condition_ref=macro.build_condition("Classification", [4, 5, 6, 17, 67]),
        condition_out=f"{dsm_dimension}=0",
    )
    # 4.2 Particularité de reprise des points sol au plus près des bâtiments
    pipeline = macro.add_radius_assign(
        pipeline,
        1.25,
        False,
        condition_src="Classification==2 && PT_VEG_DSM==0",
        condition_ref=macro.build_condition("Classification", [6, 67]),
        condition_out="PT_CLOSED_BUILDING=1",
    )
    pipeline = macro.add_radius_assign(
        pipeline,
        1,
        False,
        condition_src=f"Classification==2 && {dsm_dimension}==0 && PT_CLOSED_BUILDING==1 && {dtm_dimension}==1",
        condition_ref="Classification==2 && PT_CLOSED_BUILDING==0 && PT_VEG_DSM==0",
        condition_out=f"{dsm_dimension}=1",
    )
    ###################################################################################################################
    # 5 - Gestion des classes sous les ponts pour être détaguées pour le MNS dsm_dimension=0
    ###################################################################################################################

    pipeline = macro.add_radius_assign(
        pipeline,
        1.5,
        False,
        condition_src=macro.build_condition("Classification", [2, 3, 4, 5, 6, 9, 67]),
        condition_ref="Classification==17",
        condition_out="PT_UNDER_BRIDGE=1",
        max2d_above=-1,  # prendre les points (condition_src) qui on des points ponts au dessus d'eux (condition_ref)
        max2d_below=0,
    )
    pipeline = macro.add_radius_assign(
        pipeline,
        1.25,
        False,
        condition_src="PT_UNDER_BRIDGE==1",
        condition_ref="PT_UNDER_BRIDGE==0 && "
        + macro.build_condition("Classification", [2, 3, 4, 5, 6, 9, 67]),
        condition_out="PT_UNDER_BRIDGE=0",
        max2d_above=0.5,
        max2d_below=0.5,
    )
    pipeline |= pdal.Filter.assign(value=[f"{dsm_dimension}=0 WHERE PT_UNDER_BRIDGE==1"])
    ###################################################################################################################
    # 6 - Ajout des point pour MNT (sol) qui servent au MNS également
    ###################################################################################################################

    pipeline |= pdal.Filter.assign(
        value=[
            f"{dsm_dimension}=1 WHERE ({dtm_dimension}==1 && PT_VEG_DSM==0 && PT_UNDER_BRIDGE==0 && PT_CLOSED_BUILDING==0 && PT_UNDER_VEGET==0)"
        ]
    )

    ###################################################################################################################
    # 7 - Gestion des pts virtuels 66 pont et eau / MNT et MNS
    ###################################################################################################################
    # Taguage pour les MNT de tous les points virtuels
    # Gestion des pts virtuels qui sont sous la végétation ou autres pour le MNS
    # Taguage pour les MNS des points vituels "eau" seulement

    # 7.1 Taguade pour les MNT des points virtuels ponts et eau
    pipeline |= pdal.Filter.assign(value=[f"{dtm_dimension}=1 WHERE Classification==66"])
    # 7.2 gestion des pts 66 "eau" sous le sursol
    pipeline = macro.add_radius_assign(
        pipeline,
        0.5,
        False,
        condition_src="Classification==66",
        condition_ref=macro.build_condition("Classification", [4, 5, 6, 17, 67]),
        condition_out="PT_UNDER_VEGET=1",
    )
    pipeline = macro.add_radius_assign(
        pipeline,
        0.5,
        False,
        condition_src="PT_UNDER_VEGET==1 && Classification==66",
        condition_ref="PT_UNDER_VEGET==0 && Classification==66",
        condition_out="PT_UNDER_VEGET=0",
    )
    # 7.3 Taguage pour les MNS des points virtuels eau seulement
    pipeline = macro.add_radius_assign(
        pipeline,
        0.5,
        False,
        condition_src="Classification==66",
        condition_ref="Classification==17",
        condition_out="PT_UNDER_BRIDGE=1",
    )
    pipeline |= pdal.Filter.assign(
        value=[
            f"{dsm_dimension}=1 WHERE (Classification==66 && PT_UNDER_VEGET==0 && PT_UNDER_BRIDGE==0)"
        ]
    )

    ##################################################################################################################
    # 8 - export du nuage et des DSM
    ###################################################################################################################
    pipeline |= pdal.Writer.las(
        extra_dims="all", forward="all", filename=output_las, minor_version="4"
    )

    return pipeline, temporary_dimensions


def mark_points_to_use_for_digital_models_with_new_dimension(
    input_las,
    output_las,
    dsm_dimension,
    dtm_dimension,
    output_dsm,
    output_dtm,
    keep_temporary_dimensions=False,
):
    with tempfile.NamedTemporaryFile(suffix="_with_temporary_dims.las", dir=".") as tmp_las:
        pipeline, temporary_dimensions = define_marking_pipeline(
            input_las,
            tmp_las.name,
            dsm_dimension,
            dtm_dimension,
        )

        if output_dtm:
            pipeline |= pdal.Writer.gdal(
                gdaldriver="GTiff",
                output_type="max",
                resolution=0.5,
                filename=output_dtm,
                where=f"{dtm_dimension}==1",
            )

        if output_dsm:
            pipeline |= pdal.Writer.gdal(
                gdaldriver="GTiff",
                output_type="max",
                resolution=0.5,
                filename=output_dsm,
                where=f"{dsm_dimension}==1",
            )

        pipeline.execute()

        if keep_temporary_dimensions:
            shutil.copy(tmp_las.name, output_las)
        else:
            remove_dimensions_from_las(
                tmp_las.name,
                temporary_dimensions + ["SRC_DOMAIN", "REF_DOMAIN", "radius_search"],
                output_las,
            )


def main(
    input_las,
    output_las,
    dsm_dimension,
    dtm_dimension,
    output_dsm,
    output_dtm,
    keep_temporary_dims=False,
    skip_buffer=False,
    buffer_width=25,
    spatial_ref="EPSG:2154",
    tile_width=1000,
    tile_coord_scale=1000,
):
    if skip_buffer:
        mark_points_to_use_for_digital_models_with_new_dimension(
            input_las,
            output_las,
            dsm_dimension,
            dtm_dimension,
            output_dsm,
            output_dtm,
            keep_temporary_dims,
        )
    else:
        mark_with_buffer = run_on_buffered_las(
            buffer_width, spatial_ref, tile_width, tile_coord_scale
        )(mark_points_to_use_for_digital_models_with_new_dimension)

        mark_with_buffer(
            input_las,
            output_las,
            dsm_dimension,
            dtm_dimension,
            output_dsm,
            output_dtm,
            keep_temporary_dims,
        )


if __name__ == "__main__":
    args = parse_args()
    main(**vars(args))
