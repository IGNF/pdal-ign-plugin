import pdal
import os
import subprocess

os.environ["PDAL_DRIVER_PATH"] = os.path.abspath('./install/lib')

def pdal_has_plugin(name_filter):
    result = subprocess.run(['pdal', '--drivers'], stdout=subprocess.PIPE)
    if name_filter not in result.stdout.decode('utf-8'):
        raise ValueError("le script " + name_filter + " n'est pas visible")
