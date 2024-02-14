
file( GLOB_RECURSE GD_SRCS 
	${CMAKE_SOURCE_DIR}/src/filter_radius_search/*.hpp
	${CMAKE_SOURCE_DIR}/src/filter_radius_search/*.cpp)

PDAL_CREATE_PLUGIN(
    TYPE filter
    NAME radius_search
    VERSION 1.0
    SOURCES ${GD_SRCS}
)

install(TARGETS
	pdal_plugin_filter_radius_search
)

