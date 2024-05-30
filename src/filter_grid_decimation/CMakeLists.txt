
file( GLOB_RECURSE GD_SRCS 
	${CMAKE_SOURCE_DIR}/src/filter_grid_decimation/*.hpp
	${CMAKE_SOURCE_DIR}/src/filter_grid_decimation/*.cpp)

PDAL_CREATE_PLUGIN(
    TYPE filter
    NAME grid_decimation
    VERSION 1.0
    SOURCES ${GD_SRCS}
)

install(TARGETS
	pdal_plugin_filter_grid_decimation
)

