cmake_minimum_required( VERSION 3.5 )

set(CMAKE_TRY_COMPILE_TARGET_TYPE "STATIC_LIBRARY")

project(MY_READER LANGUAGES CXX)

set(CMAKE_PREFIX_PATH ${CONDA_PREFIX})
set(CMAKE_XCODE_ATTRIBUTE_OTHER_CODE_SIGN_FLAGS "-o linker-signed")

# Set library prefix to "lib"
set(CMAKE_SHARED_LIBRARY_PREFIX "lib")
set(CMAKE_STATIC_LIBRARY_PREFIX "lib")

find_package(PDAL REQUIRED)

if(NOT CMAKE_INSTALL_PREFIX)
    set(CMAKE_INSTALL_PREFIX ${CMAKE_SOURCE_DIR}/install)
endif()
set(CMAKE_DEBUG_POSTFIX d)

## add plugin
add_subdirectory(src/filter_grid_decimation)
add_subdirectory(src/filter_radius_assign)

