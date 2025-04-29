import argparse

import pdal

from pdal_ign_macro import macro


def parse_args():
    parser = argparse.ArgumentParser("Tool to correct fields classification")
    parser.add_argument("--input", "-i", type=str, required=True, help="Input las file")
    parser.add_argument(
        "--output_las", "-o", type=str, required=True, help="Output cloud las file"
    )
    parser.add_argument("--in_vec_fields", "-v", type=str, required=True, help="Input vector file")

    # for debug
    parser.add_argument("--output_dsm", "-s", type=str, required=True, help="Output dsm tiff file")
    parser.add_argument("--output_dtm", "-t", type=str, required=True, help="Output dtm tiff file")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    pipeline = pdal.Reader.las(args.input)

    # FnScanClassifyShapes("2", 100, 0, 10, 0, 0, 0, 0, 0, 0, 0.000, 0)
    # les points sol contenus dans les vecteurs en classe 100
    pipeline |= pdal.Filter.classify_by_geo(
        datasource=args.in_vec_fields, src_domain=[2], new_class_value=100
    )

    # FnScanClassifyShapes("3-5", 102, 0, 10, 0, 0, 0, 0, 0, 0, 20.000, 0)
    # les points veget contenus dans les vecteurs (avec buffer de 20m) en classe 102
    pipeline |= pdal.Filter.classify_by_geo(
        datasource=args.in_vec_fields, src_domain=[3, 5], new_class_value=102, buffer=20.0
    )
    # FnScanThinGrid2d("100", 101, 0, 0, 3.000, 0)
    # le point sol (100) le plus haut de chaque cellule de la grille en 101
    macro.classify_thin_grid_2d(
        pipeline=pipeline,
        condition="Classification==100",
        assignment_out="Classification=101",
        grid_size=3.0,
        mode="max",
    )

    # FnScanThinGrid2d("102", 5, 0, 0, 3.000, 0)
    # le point veget le plus haut de chaque cellule de la grille en veget haute (5)
    macro.classify_thin_grid_2d(
        pipeline=pipeline,
        condition="Classification==102",
        assignment_out="Classification=5",
        grid_size=3.0,
        mode="max",
    )

    # FnScanDistClass("101", "100")
    # distance entre le point le plus haut (101) et le reste du sol (100) (en gros le premier point sol de son voisinage)
    # FnScanClassifyDistance("101", 103, -4.000, -0.400, 0)
    # si le point le plus haut du sol (101) des cellules est ds [-4.000, -0.400Ø], on le passe en 103
    pipeline |= pdal.Filter.classify_by_distance(
        src_domain=101,
        reference_domain=100,
        new_class_value=103,
        distance_min=0.4,
        distance_max=4,
        only_bellow=True,
    )

    # FnScanDistClass("101", "102")
    # distance entre le point le plus haut (101) et la veget (102) (en gros le premier point sol de son voisinage)
    # ceux que l'on a pas reclassé dans l'étapde précédente
    # FnScanClassifyDistance("101", 103, -4.000, -0.400, 0)
    # si le point le plus haut du sol (101) des cellules est ds [-4.000, -0.400Ø], on le passe en 103
    pipeline |= pdal.Filter.classify_by_distance(
        src_domain=101,
        reference_domain=102,
        new_class_value=103,
        distance_min=0.4,
        distance_max=4,
        only_bellow=True,
    )

    # FnScanThinGrid2d("103", 101, 1, 0, 15.000, 0)
    # le point 103 le plus bas de chaque cellule de la grille (de 15m) en 103
    macro.classify_thin_grid_2d(
        pipeline=pipeline,
        condition="Classification==103",
        assignment_out="Classification=101",
        grid_size=15.0,
        mode="min",
    )

    # FnScanClassifyHgtLst("2,103", 200.0, 101, 2, -0.100, 0.100, 0)
    # les points 101 (initialement sol ?) prochent du sol (2, 103) basculent en sol
    macro.classify_hgt_ground_list(
        pipeline=pipeline,
        class_ground=[2, 103],
        h_min=-0.100,
        h_max=0.100,
        condition="Classification==101",
        assignment_out="Classification=2",
    )

    # les points 103 rebasculent en sol (2)
    # FnScanClassifyClass("103", 2, 0)
    pipeline |= pdal.Filter.assign(value="Classification=2", where="Classification==103")

    # les points 100,101,102 rebasculent en veget haute (5)
    # FnScanClassifyClass("100-102",5,0)
    pipeline |= pdal.Filter.assign(
        value="Classification=5", where=macro.build_condition("Classification", [100, 101, 102])
    )

    # FnScanDistClass("5", "2")
    # FnScanClassifyHgtGrd(2, 100.0, 5, 3, 0.000, 0.500, 0)
    # FnScanClassifyHgtGrd(2, 100.0, 5, 4, 0.500, 1.500, 0)
    macro.classify_hgt_ground(
        pipeline, 0.0, 0.5, condition="Classification==5", assignment_out="Classification=3"
    )
    macro.classify_hgt_ground(
        pipeline, 0.5, 1.5, condition="Classification==5", assignment_out="Classification=4"
    )

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
