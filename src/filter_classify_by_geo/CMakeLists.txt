
file( GLOB_RECURSE GD_SRCS 
	${CMAKE_SOURCE_DIR}/src/filter_classify_by_geo/*.hpp
	${CMAKE_SOURCE_DIR}/src/filter_classify_by_geo/*.cpp)

PDAL_CREATE_PLUGIN(
    TYPE filter
    NAME classify_by_geo
    VERSION 1.0
    SOURCES ${GD_SRCS}
)

target_link_libraries(pdal_plugin_filter_classify_by_geo PRIVATE ${GDAL_LIBRARIES})

install(TARGETS
	pdal_plugin_filter_classify_by_geo
)
