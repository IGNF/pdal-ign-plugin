# PlugIn IGN for PDAL

## Compile

You need to have conda!

Create the ign_pdal_tools conda environment using the `environment.yml` file
to be able to run the compilation in this environment.

### linux/mac

run ci/build.sh

Set the `PDAL_DRIVER_PATH` environment variable to point to `${THIS REPO}/install/lib`
in order for pdal to find the plugins.

### Windows

one day, maybe...

## Architecture of the code

The code is structured as:

```
├── src
│   ├── plugin folder
│   │   ├── pluginFilter.cpp
│   │   ├── pluginFilter.h
│   │   ├── CMakeLists.txt
├── doc
│   ├── pluginFilter.md
├── examples  # examples of usage of the code or the docker image
├── ci
├── pdal_ign_macro  # Python module with ready-to-use filters combinations
│   ├── __init__.py
│   ├── macro.py
│   ├── version.py
│   └── *.py  # Example scripts to use the plugin filters + the filters combinations contained in `macro`
├── test
├── CMakeLists.txt
├── environment*.yml
├── Dockerfile
├── pyproject.toml  # Setup file to install the `macro` python module with pip
├── .github
└── .gitignore
```

## Run the tests

Each plugin should have his own test. To run all tests:

```
python -m pytest -s
```

## List of Filters

[grid decimation](./doc/grid_decimation.md) [Deprecated: use the gridDecimation filter from the pdal repository]

[radius assign](./doc/radius_assign.md)

## Adding a filter

In order to add a filter, you have to add a new folder in the src directory :

```
├── src
│   ├── filter_my_new_PI
│   │   ├── my_new_PI_Filter.cpp
│   │   ├── my_new_PI_Filter.h
│   │   ├── CMakeLists.txt
```

The name of the folder informs of the plugIN nature (reader, writer, filter).

The code should respect the documentation proposed by pdal: [build a pdal plugin](https://pdal.io/en/2.6.0/development/plugins.html).
Be careful to change if the plugIn is a reader, a writer or a filter.

The CMakeList should contain:

```
file( GLOB_RECURSE GD_SRCS ${CMAKE_SOURCE_DIR} *)

PDAL_CREATE_PLUGIN(
    TYPE filter
    NAME my_new_PI
    VERSION 1.0
    SOURCES ${GD_SRCS}
)

install(TARGETS pdal_plugin_filter_my_new_PI)
```

You should complete the main CMakeList by adding the new plugIN:
```
add_subdirectory(src/filter_my_new_PI)
```

Each plugIN has his own md file in the doc directory, structured as the [model](./doc/_doc_model_plugIN.md).

Don't forget to update [the list](#list-of-filters) with a link to the documentation.

## `macro` python module usage

The `macro` python module is installed in the project docker image so that it can be imported from anywhere in the
docker image.


### Syntax to use it in a python script

```python
from pdal_ign_macro import macro

marco.my_macro(...)
```

See the `scripts` folder for example usages of this module.

## Docker

There are two docker files. 

    - The main Dockerfile use the official pdal version. 
    - The Dockerfile.pdal permit to use non official version of pdal (the master or a fork for exemple). See the "docker-build-pdal" command in  Makefile 

### Usage from outside the docker image:

If you have a python script on your computer, you can mount its containing folder as a volume in order to
run it in the docker image.

Example:

```bash
docker run \
    -v /my/data/folder:/data \
    -v  /my/output/folder:/output \
    -v /my/script/folder:/scripts \
    pdal_ign_plugin \
    python /scripts/my_script.py --input /data/my_data_file.las -o /output/my_output.las
```

Another example can be found in the [./example](./examples/) folder:

Run the following command to run the [demo_script](./examples/demo_script.py) python script
which copies an input las file into the output folder as a las1.4 file :

```bash
./examples/run_custom_script_in_docker_image.sh -i ./test/data/mnx/input/bat.laz -o ./tmp/demo -s ./examples/demo_script.py
```
