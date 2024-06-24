import argparse

import pdal

from pdal_ign_macro import macro

"""
This tool applies a pdal pipeline to select points for DSM and DTM calculation
It adds dimensions with positive values for the selected points
"""


def parse_args():
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
    return parser.parse_args()


def mark_points_to_use_for_digital_models_with_new_dimension(
    input_las, output_las, dsm_dimension, dtm_dimension, output_dsm, output_dtm
):
    pipeline = pdal.Pipeline() | pdal.Reader.las(input_las)

    # 0 - ajout de dimensions temporaires et de sortie
    added_dimensions = [dtm_dimension, dsm_dimension, "PT_VEG_DSM", "PT_ON_BRIDGE"]
    pipeline |= pdal.Filter.ferry(dimensions="=>" + ", =>".join(added_dimensions))

    # 1 - recherche des points max de végétation (4,5) sur une grille régulière, avec prise en
    # compte des points sol (2) et basse
    #     vegetation (3) proche de la végétation
    #     pour le calcul du DSM

    pipeline |= pdal.Filter.assign(
        value=["PT_VEG_DSM = 1 WHERE " + macro.build_condition("Classification", [4, 5])]
    )

    # bouche trou : assigne les points sol à l'intérieur de la veget (4,5)
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
        condition_ref="Classification==2",
        condition_out="PT_VEG_DSM=0",
    )

    # selection des points de veget basse proche de la veget haute
    pipeline = macro.add_radius_assign(
        pipeline,
        1,
        False,
        condition_src="Classification==3",
        condition_ref="Classification==5",
        condition_out="PT_VEG_DSM=1",
    )

    # max des points de veget (PT_VEG_DSM==1) sur une grille régulière :
    # TODO: remplacer par GridDecimation une fois le correctif mergé dans PDAL
    # pipeline |= pdal.Filter.GridDecimation(
    #     resolution=0.75, value=f"{dsm_dimension}=1", output_type="max", where="PT_VEG_DSM==1"
    # )
    pipeline |= pdal.Filter.grid_decimation_deprecated(
        resolution=0.75, output_dimension=dsm_dimension, output_type="max", where="PT_VEG_DSM==1"
    )

    # 2 - sélection des points pour DTM et DSM

    # selection de points DTM (max) sur une grille régulière
    # TODO: remplacer par GridDecimation une fois le correctif mergé dans PDAL
    # pipeline |= pdal.Filter.GridDecimation(
    #     resolution=0.5, value=f"{dtm_dimension}=1", output_type="max", where="Classification==2"
    # )
    pipeline |= pdal.Filter.grid_decimation_deprecated(
        resolution=0.5,
        output_dimension=dtm_dimension,
        output_type="max",
        where="Classification==2",
    )

    # selection de points DSM (max) sur une grille régulière
    # TODO: remplacer par GridDecimation une fois le correctif mergé dans PDAL
    # pipeline |= pdal.Filter.GridDecimation(
    #     resolution=0.5,
    #     value=f"{dsm_dimension}=1",
    #     output_type="max",
    #     where="("
    #     + macro.build_condition("Classification", [6, 9, 17, 64])
    #     + f") || {dsm_dimension}==1",
    # )
    pipeline |= pdal.Filter.grid_decimation_deprecated(
        resolution=0.5,
        output_dimension=dsm_dimension,
        output_type="max",
        where="("
        + macro.build_condition("Classification", [6, 9, 17, 64])
        + f") || {dsm_dimension}==1",
    )

    # assigne des points sol sélectionnés : les points proches de la végétation, des ponts, de l'eau, 64
    pipeline = macro.add_radius_assign(
        pipeline,
        1.5,
        False,
        condition_src=f"{dtm_dimension}==1",
        condition_ref=macro.build_condition("Classification", [4, 5, 6, 9, 17, 64]),
        condition_out=f"{dsm_dimension}=1",
    )

    # 3 - gestion des ponts
    #     bouche trou : on filtre les points (2,3,4,5,9) au milieu du pont en les mettant à PT_ON_BRIDGE=1

    pipeline = macro.add_radius_assign(
        pipeline,
        1.5,
        False,
        condition_src=macro.build_condition("Classification", [2, 3, 4, 5, 9]),
        condition_ref="Classification==17",
        condition_out="PT_ON_BRIDGE=1",
        max2d_above=0,  # ne pas prendre les points qui sont au dessus des points pont (condition_ref)
        max2d_below=-1,  # prendre tous les points qui sont en dessous des points pont (condition_ref)
    )
    pipeline = macro.add_radius_assign(
        pipeline,
        1.5,
        False,
        condition_src="PT_ON_BRIDGE==1",
        condition_ref=macro.build_condition("Classification", [2, 3, 4, 5]),
        condition_out="PT_ON_BRIDGE=0",
    )
    pipeline |= pdal.Filter.assign(value=[f"{dsm_dimension}=0 WHERE PT_ON_BRIDGE==1"])

    # 4 - point pour DTM servent au DSM également
    pipeline |= pdal.Filter.assign(value=[f"{dsm_dimension}=1 WHERE {dtm_dimension}==1"])

    # 5 - export du nuage et des DSM
    # TODO: n'ajouter que les dimensions de sortie utiles !

    pipeline |= pdal.Writer.las(extra_dims="all", forward="all", filename=output_las)

    if output_dtm:
        pipeline |= pdal.Writer.gdal(
            gdaldriver="GTiff",
            output_type="max",
            resolution=2.0,
            filename=output_dtm,
            where=f"{dtm_dimension}==1",
        )

    if output_dsm:
        pipeline |= pdal.Writer.gdal(
            gdaldriver="GTiff",
            output_type="max",
            resolution=2.0,
            filename=output_dsm,
            where=f"{dsm_dimension}==1",
        )

    pipeline.execute()


if __name__ == "__main__":
    args = parse_args()
    mark_points_to_use_for_digital_models_with_new_dimension(**vars(args))
