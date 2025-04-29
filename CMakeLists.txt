cmake_minimum_required( VERSION 3.5 )

project(MY_READER LANGUAGES CXX)

set(CMAKE_PREFIX_PATH ${CONDA_PREFIX})
set(CMAKE_XCODE_ATTRIBUTE_OTHER_CODE_SIGN_FLAGS "-o linker-signed")

find_package(PDAL REQUIRED)
find_package(GDAL REQUIRED)

set(CMAKE_INSTALL_PREFIX ${CMAKE_SOURCE_DIR}/install)
set(CMAKE_DEBUG_POSTFIX d)

## add plugin
add_subdirectory(src/filter_grid_decimation)
add_subdirectory(src/filter_radius_assign)
add_subdirectory(src/filter_classify_by_geo)
add_subdirectory(src/filter_classify_by_distance)