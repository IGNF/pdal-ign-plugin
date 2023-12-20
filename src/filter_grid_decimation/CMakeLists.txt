
file( GLOB_RECURSE GD_SRCS ${CMAKE_SOURCE_DIR} *)

message("GD_SRCS ${GD_SRCS}")

PDAL_CREATE_PLUGIN(
    TYPE filter
    NAME grid_decimation
    VERSION 1.0
    SOURCES ${GD_SRCS}
)

install(TARGETS
	pdal_plugin_filter_grid_decimation
)

