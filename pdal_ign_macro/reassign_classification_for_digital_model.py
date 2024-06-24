import argparse

import pdal

from pdal_ign_macro import macro

"""
This tool shows how to use functions of macro in a pdal pipeline
"""


def parse_args():
    parser = argparse.ArgumentParser("Tool to apply pdal pipelines for DSM and DTM calculation")
    parser.add_argument("--input", "-i", type=str, required=True, help="Input las file")
    parser.add_argument(
        "--output_las", "-o", type=str, required=True, help="Output cloud las file"
    )
    parser.add_argument("--output_dsm", "-s", type=str, required=True, help="Output dsm tiff file")
    parser.add_argument("--output_dtm", "-t", type=str, required=True, help="Output dtm tiff file")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    pipeline = pdal.Reader.las(args.input)

    # 1 - recherche des points max de végétation (4,5) sur une grille régulière, avec prise en compte des points sol (2) et basse
    #     vegetation (3) proche de la végétation : on les affecte en 100

    # bouche trou : assigne les points sol en 102 à l'intérieur de la veget (4,5)
    pipeline = macro.add_radius_assign(
        pipeline,
        1,
        False,
        condition_src="Classification==2",
        condition_ref=macro.build_condition("Classification", [4, 5]),
        condition_out="Classification=102",
    )
    pipeline = macro.add_radius_assign(
        pipeline,
        1,
        False,
        condition_src="Classification==102",
        condition_ref="Classification==2",
        condition_out="Classification=2",
    )

    # selection des points de veget basse proche de la veget haute : assigne 103
    pipeline = macro.add_radius_assign(
        pipeline,
        1,
        False,
        condition_src="Classification==3",
        condition_ref="Classification==5",
        condition_out="Classification=103",
    )

    # max des points de veget (et surement veget - 102,103) sur une grille régulière : assigne 100
    pipeline |= pdal.Filter.gridDecimation(
        resolution=0.75,
        value="Classification=100",
        output_type="max",
        where=macro.build_condition("Classification", [4, 5, 102, 103]),
    )

    # remise à zero des codes 102 et 103
    pipeline |= pdal.Filter.assign(value="Classification=2", where="Classification==102")
    pipeline |= pdal.Filter.assign(value="Classification=3", where="Classification==103")

    # 2 - sélection des points pour DTM et DSM

    # selection de points sol (max) sur une grille régulière
    pipeline |= pdal.Filter.gridDecimation(
        resolution=0.5, value="Classification=102", output_type="max", where="Classification==2"
    )

    # selection de points DSM (max) sur une grille régulière
    pipeline |= pdal.Filter.gridDecimation(
        resolution=0.5,
        value="Classification=200",
        output_type="max",
        where=macro.build_condition("Classification", [2, 3, 4, 5, 6, 9, 17, 64, 100]),
    )

    # assigne des points sol sélectionnés (102) en 100 : les points proches de la végaétation, des ponts, de l'eau et 64
    pipeline = macro.add_radius_assign(
        pipeline,
        1.5,
        False,
        condition_src="Classification==102",
        condition_ref=macro.build_condition("Classification", [4, 5, 6, 9, 17, 64, 100]),
        condition_out="Classification=100",
    )

    # remise à zero du code 102
    pipeline |= pdal.Filter.assign(value="Classification=2", where="Classification==102")

    # 3 - gestion des ponts

    # bouche trou : on élimine les points sol (2) au milieu du pont en les mettant à 102
    pipeline = macro.add_radius_assign(
        pipeline,
        1.5,
        False,
        condition_src="Classification==2",
        condition_ref="Classification==17",
        condition_out="Classification=102",
    )
    pipeline = macro.add_radius_assign(
        pipeline,
        1.5,
        False,
        condition_src="Classification==102",
        condition_ref=macro.build_condition("Classification", [2, 3, 4, 5]),
        condition_out="Classification=2",
    )

    # bouche trou : on élimine les points basse végétation (3) au milieu du pont en les mettant à 103
    pipeline = macro.add_radius_assign(
        pipeline,
        1.5,
        False,
        condition_src="Classification==3",
        condition_ref="Classification==17",
        condition_out="Classification=103",
    )
    pipeline = macro.add_radius_assign(
        pipeline,
        1.5,
        False,
        condition_src="Classification==103",
        condition_ref=macro.build_condition("Classification", [2, 3, 4, 5]),
        condition_out="Classification=3",
    )

    # bouche trou : on élimine les points moyenne végétation (4) au milieu du pont en les mettant à 104
    pipeline = macro.add_radius_assign(
        pipeline,
        1.5,
        False,
        condition_src="Classification==4",
        condition_ref="Classification==17",
        condition_out="Classification=104",
    )
    pipeline = macro.add_radius_assign(
        pipeline,
        1.5,
        False,
        condition_src="Classification==104",
        condition_ref=macro.build_condition("Classification", [2, 3, 4, 5]),
        condition_out="Classification=4",
    )

    # bouche trou : on élimine les points haute végétation (5) au milieu du pont en les mettant à 105
    pipeline = macro.add_radius_assign(
        pipeline,
        1.5,
        False,
        condition_src="Classification==5",
        condition_ref="Classification==17",
        condition_out="Classification=105",
    )
    pipeline = macro.add_radius_assign(
        pipeline,
        1.5,
        False,
        condition_src="Classification==105",
        condition_ref=macro.build_condition("Classification", [2, 3, 4, 5]),
        condition_out="Classification=5",
    )

    # bouche trou : on élimine les points eau (9) au milieu du pont en les mettant à 109
    pipeline = macro.add_radius_assign(
        pipeline,
        1.5,
        False,
        condition_src="Classification==9",
        condition_ref="Classification==17",
        condition_out="Classification=109",
    )
    pipeline = macro.add_radius_assign(
        pipeline,
        1.5,
        False,
        condition_src="Classification==109",
        condition_ref="Classification==9",
        condition_out="Classification=9",
    )

    # step 15 et supression des points ??

    # 4 - export du nuage
    pipeline |= pdal.Writer.las(extra_dims="all", forward="all", filename=args.output_las)

    # export des DSM/DTM
    pipeline |= pdal.Writer.gdal(
        gdaldriver="GTiff",
        output_type="max",
        resolution=2.0,
        filename=args.output_dtm,
        where=macro.build_condition("Classification", [2, 66]),
    )
    pipeline |= pdal.Writer.gdal(
        gdaldriver="GTiff",
        output_type="max",
        resolution=2.0,
        filename=args.output_dsm,
        where=macro.build_condition("Classification", [2, 3, 4, 5, 17, 64]),
    )

    pipeline.execute()
