import os
import subprocess


def pdal_has_plugin(name_filter):
    print("Initialize pdal driver : ", os.environ["PDAL_DRIVER_PATH"])
    result = subprocess.run(["pdal", "--drivers"], stdout=subprocess.PIPE)
    if name_filter not in result.stdout.decode("utf-8"):
        raise ValueError("Filter " + name_filter + " not found by `pdal --drivers`.")
