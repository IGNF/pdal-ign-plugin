cmake_minimum_required( VERSION 3.5 )

project(MY_READER LANGUAGES CXX)

set(CMAKE_PREFIX_PATH ${CONDA_PREFIX})

find_package(PDAL REQUIRED)

set(CMAKE_INSTALL_PREFIX ${CMAKE_SOURCE_DIR}/install)
set(CMAKE_DEBUG_POSTFIX d)

## add plugin
add_subdirectory(src/filter_grid_decimation)

