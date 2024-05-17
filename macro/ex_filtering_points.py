import argparse
import pdal
import macro

"""
This tool shows how to use functions of macro in a pdal pipeline
"""

def parse_args():
    parser = argparse.ArgumentParser("Tool to apply pdal pipelines to modify classification")
    parser.add_argument("--input", "-i", type=str, required=True, help="Input las file")
    parser.add_argument("--output", "-o", type=str, required=True, help="Output las file")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    pipeline = pdal.Reader.las(args.input)

    # step 1 a 9
    pipeline = macro.add_radius_assign(pipeline, 1, False, "Classification==2", macro.build_condition("Classification", [4,5]), "Classification=102")
    pipeline = macro.add_radius_assign(pipeline, 1, False, "Classification==102", "Classification==2", "Classification=2")
    pipeline = macro.add_radius_assign(pipeline, 1, False, "Classification==3", "Classification==5", "Classification=103")
    pipeline = macro.add_grid_decimation(pipeline, 0.75, "max", macro.build_condition("Classification", [4,5,102,103]), "Classification=100")
    pipeline |= pdal.Filter.assign(value="Classification=2", where="Classification==102")
    pipeline |= pdal.Filter.assign(value="Classification=3", where="Classification==103")
    pipeline = macro.add_grid_decimation(pipeline, 0.5, "max", "Classification==2", "Classification=102")
    pipeline = macro.add_grid_decimation(pipeline, 0.5, "max", macro.build_condition("Classification", [2,3,4,5,6,9,17,64,100]), "Classification=200")
    pipeline = macro.add_radius_assign(pipeline, 1.5, False, "Classification==102", macro.build_condition("Classification", [4,5,6,9,17,64,100]), "Classification=100")
    pipeline |= pdal.Filter.assign(value="Classification=2", where="Classification==102")

    # step 10
    pipeline = macro.add_radius_assign(pipeline, 1.5, False, "Classification==2", "Classification==17", "Classification=102")
    pipeline = macro.add_radius_assign(pipeline, 1.5, False, "Classification==102", macro.build_condition("Classification", [2,3,4,5]), "Classification=2")

    # step 11
    pipeline = macro.add_radius_assign(pipeline, 1.5, False, "Classification==3", "Classification==17", "Classification=103")
    pipeline = macro.add_radius_assign(pipeline, 1.5, False, "Classification==103", macro.build_condition("Classification", [2,3,4,5]), "Classification=3")

    # step 12
    pipeline = macro.add_radius_assign(pipeline, 1.5, False, "Classification==4", "Classification==17", "Classification=104")
    pipeline = macro.add_radius_assign(pipeline, 1.5, False, "Classification==104", macro.build_condition("Classification", [2,3,4,5]), "Classification=4")

    # step 13
    pipeline = macro.add_radius_assign(pipeline, 1.5, False, "Classification==5", "Classification==17", "Classification=105")
    pipeline = macro.add_radius_assign(pipeline, 1.5, False, "Classification==105", macro.build_condition("Classification", [2,3,4,5]), "Classification=5")

    # step 14
    pipeline = macro.add_radius_assign(pipeline, 1.5, False, "Classification==9", "Classification==17", "Classification=109")
    pipeline = macro.add_radius_assign(pipeline, 1.5, False, "Classification==109", "Classification==9", "Classification=9")

    pipeline |= pdal.Writer.las(extra_dims="all",minor_version=4,dataformat_id=6,filename=args.output)
    pipeline.execute()

