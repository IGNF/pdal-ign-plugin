cmake_minimum_required( VERSION 3.5 )

project(MY_READER LANGUAGES CXX)

set(CMAKE_PREFIX_PATH ${CONDA_PREFIX})

find_package(PDAL REQUIRED)

set(CMAKE_INSTALL_PREFIX ${CMAKE_SOURCE_DIR}/install)
set(CMAKE_DEBUG_POSTFIX d)

#########  filter - gridDecimation #########

file( GLOB_RECURSE GD_SRCS ${CMAKE_SOURCE_DIR} src/filter_grid_decimation/*.*)

PDAL_CREATE_PLUGIN(
    TYPE filter
    NAME grid_decimation
    VERSION 1.0
    SOURCES ${GD_SRCS}
)


######### Install  ######### 

install(TARGETS
	pdal_plugin_filter_grid_decimation
)

