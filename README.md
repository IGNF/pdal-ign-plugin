# PlugIn IGN for PDAL

## Compile

You need to have conda ! 

### linux/mac

run ci/build.sh

### Windows 

todo...

## Architecture of the code

The code is structured as :

```
├── src
│   ├── plugins forlder
│   │   ├── plufinFilter.cpp
│   │   ├── plufinFilter.h
│   │   ├── CMakeLisits.txt
├── doc
│   ├── plufinFilter.md
├── ci
├── test
├── CMakeLisits.txt
├── environment*.yml
├── Dockerfile 
├── .github 
└── .gitignore
```

## Run the tests

Each plugin should have his own test. To run test :

```
python -m pytest -s
```

## List of Filters

[grid decimation](./doc/grid_decimation.md)

## Adding a filter

In order to add a filter, you have to add a new folder in the src directory : 

```
├── src
│   ├── filter_my_new_PI
│   │   ├── my_new_PI_Filter.cpp
│   │   ├── my_new_PI_Filter.h
│   │   ├── CMakeLisits.txt
```

The name of the folder informs of the plugIN nature (reader, writer, filter).

The code should respect the documentation purpose by pdal : [build a pdal plugin](https://pdal.io/en/2.6.0/development/plugins.html). Be careful to change if the plugIn is a reader, a writer or a filter. 

The CMakeList should contains : 

```
file( GLOB_RECURSE GD_SRCS ${CMAKE_SOURCE_DIR} src/my_new_PI/*.*)

PDAL_CREATE_PLUGIN(
    TYPE filter
    NAME my_new_PI
    VERSION 1.0
    SOURCES ${GD_SRCS}
)

install(TARGETS pdal_plugin_filter_my_new_PI)
```

You should complet the principal CMakeList by adding the new plugIN :
 
```
add_subdirectory(src/filter_my_new_PI)
```

Each plugIN has his own md file in the doc directory, structured as the [model](./doc/_doc_model_plugIN.md). 

D'ont forget to update [the list](#list-of-filters) with a link with the documentation.


 
