import argparse
import pdal
import macro

"""
This tool shows how to use functions of macro in a pdal pipeline
"""

def parse_args():
    parser = argparse.ArgumentParser("Tool to apply pdal pipelines to modify classification")
    parser.add_argument("--input", "-i", type=str, required=True, help="Input las file")
    parser.add_argument("--output_las", "-o", type=str, required=True, help="Output cloud las file")
    parser.add_argument("--output_dsm", "-s", type=str, required=True, help="Output dsm tiff file")
    parser.add_argument("--output_dtm", "-t", type=str, required=True, help="Output dtm tiff file")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    pipeline = pdal.Reader.las(args.input)

    ## 1 - recherche des points max de végétation (4,5) sur une grille régulière, avec prise en compte des points sol (2) et basse
    ##     vegetation (3) proche de la végétation
    ##     pour le calcul du DSM

    pipeline |= pdal.Filter.ferry(dimensions=f"=>PT_GRID_DSM, =>PT_DSM, =>PT_GRID_DTM")
    pipeline |= pdal.Filter.assign(value=["PT_DSM = 1 WHERE " + macro.build_condition("Classification", [4,5])])

    # bouche trou : assigne les points sol à l'intérieur de la veget (4,5)
    pipeline = macro.add_radius_assign(pipeline, 1, False, condition_src="Classification==2", condition_ref=macro.build_condition("Classification", [4,5]), condition_out="PT_DSM=1")
    pipeline = macro.add_radius_assign(pipeline, 1, False, condition_src="PT_DSM==1 && Classification==2", condition_ref="Classification==2", condition_out="Classification=2")

    # selection des points de veget basse proche de la veget haute
    pipeline = macro.add_radius_assign(pipeline, 1, False, condition_src="Classification==3", condition_ref="Classification==5", condition_out="PT_DSM=1")

    # max des points de veget (et surement veget) sur une grille régulière :
    pipeline |= pdal.Filter.gridDecimation(resolution=0.75, value="PT_GRID_DSM=1", output_type="max", where="PT_DSM==1")


    ## 2 - sélection des points pour DTM et DSM

    # selection de points DTM (max) sur une grille régulière
    pipeline |= pdal.Filter.gridDecimation(resolution=0.5, value="PT_GRID_DTM=1", output_type="max", where="Classification==2")

    # selection de points DSM (max) sur une grille régulière
    pipeline |= pdal.Filter.gridDecimation(resolution=0.5, value="PT_GRID_DSM=1", output_type="max", where=macro.build_condition("Classification", [2,3,4,5,6,9,17,64,100]))

    # assigne des points sol sélectionnés : les points proches de la végétation, des ponts, de l'eau, 64 et 100
    pipeline = macro.add_radius_assign(pipeline, 1.5, False, condition_src="PT_GRID_DTM==1",
                                       condition_ref= "(" + macro.build_condition("Classification", [4,5,6,9,17,64]) + ") && PT_GRID_DSM==1",
                                       condition_out="PT_DSM=1")


    ## 3 - gestion des ponts
    #      bouche trou : on filtre les points (2,3,4,5,9) au milieu du pont en les mettant à PT_ON_BRIDGE=1
    pipeline |= pdal.Filter.ferry(dimensions=f"=>PT_ON_BRIDGE")
    pipeline = macro.add_radius_assign(pipeline, 1.5, False, condition_src=macro.build_condition("Classification", [2,3,4,5,9]), condition_ref="Classification==17", condition_out="PT_ON_BRIDGE=1")
    pipeline = macro.add_radius_assign(pipeline, 1.5, False, condition_src="PT_ON_BRIDGE==1",
                                       condition_ref=macro.build_condition("Classification", [2,3,4,5]), condition_out="PT_ON_BRIDGE=0")

    # step 15 et supression des points ??

    # 4 - export du nuage
    pipeline |= pdal.Writer.las(extra_dims="all", minor_version=4, dataformat_id=6, filename=args.output_las)

    # export des DSM/DTM
    pipeline |= pdal.Writer.gdal(gdaldriver="GTiff", output_type="max", resolution=2.0, filename=args.output_dtm, where=macro.build_condition("Classification", [2,66]))
    pipeline |= pdal.Writer.gdal(gdaldriver="GTiff", output_type="max", resolution=2.0, filename=args.output_dsm, where=macro.build_condition("Classification", [2,3,4,5,5,17,64]))

    pipeline.execute()

