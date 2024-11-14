"""Example python script used to demonstrate the usage of local python scripts inside the pdal_ign_plugin
docker image
"""

import argparse

import pdal

from pdal_ign_macro import version as pim_version


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--input_file", type=str, help="Input las/laz file on which to run the script"
    )
    parser.add_argument("-o", "--output_file", type=str, help="Out las/laz file of the script")
    return parser.parse_args()


def main(input_file, output_file):
    print("Pdal version is:", pdal.__version__)
    print("pdal_ign_macro version is:", pim_version.__version__)
    print("Copy input file to output file as LAS1.4")
    pipeline = pdal.Pipeline()
    pipeline |= pdal.Reader.las(filename=input_file)
    pipeline |= pdal.Writer.las(filename=output_file, major_version=1, minor_version=4)
    pipeline.execute()


if __name__ == "__main__":
    args = parse_args()
    main(args.input_file, args.output_file)
