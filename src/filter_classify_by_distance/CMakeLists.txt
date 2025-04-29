
file( GLOB_RECURSE GD_SRCS 
	${CMAKE_SOURCE_DIR}/src/filter_classify_by_distance/*.hpp
	${CMAKE_SOURCE_DIR}/src/filter_classify_by_distance/*.cpp)

PDAL_CREATE_PLUGIN(
    TYPE filter
    NAME classify_by_distance
    VERSION 1.0
    SOURCES ${GD_SRCS}
)

install(TARGETS
	pdal_plugin_filter_classify_by_distance
)

