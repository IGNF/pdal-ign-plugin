# -*- coding: utf-8 -*-
"""Example python script used to demonstrate the usage of local python scripts inside models
"""
import argparse
import shutil

import pdal


from pdal_ign_macro import version as pim_version

from examples.model_hight.calculate_hight_bridge import create_highest_points_raster
from examples.model_mnt.calculate_mnt_bridge import create_mnt_points_raster


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
    
    print("Lauch Hight model")
    create_highest_points_raster(        
        input_file, 
        output_file,
        0.1,
        1000,
        1000,
        "EPSG:2154",
        -9999
    )

    print("Lauch MNT model")
    create_mnt_points_raster(
       input_file, 
        output_file,
        0.1,
        1000,
        1000,
        "EPSG:2154",
        -9999
    )


if __name__ == "__main__":
    args = parse_args()
    main(args.input_file, args.output_file)