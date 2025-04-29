/******************************************************************************
* Copyright (c) 2023, Antoine Lavenant (antoine.lavenant@ign.fr)
*
* All rights reserved.
*
****************************************************************************/

#pragma once

#include <pdal/Filter.hpp>
#include <pdal/Polygon.hpp>
#include <pdal/Streamable.hpp>

#include <map>
#include <memory>
#include <string>

typedef void *OGRLayerH;

namespace pdal
{

namespace gdal
{
    class ErrorHandler;
}

typedef std::shared_ptr<void> OGRDSPtr;
typedef std::shared_ptr<void> OGRFeaturePtr;
typedef std::shared_ptr<void> OGRGeometryPtr;

class Arg;

class ClassifyByGeoFilter : public Filter
{
    struct PolyVal
    {
        Polygon geom;
        int32_t val;
    };

public:
    ClassifyByGeoFilter() {}

    std::string getName() const { return "filters.classify_by_geo"; }

private:
    virtual void addArgs(ProgramArgs& args);
    virtual bool processOne(PointRef& point);
    virtual void initialize();
    virtual void ready(PointTableRef table);
    virtual PointViewSet run(PointViewPtr view);

    typedef std::shared_ptr<void> OGRDSPtr;

    std::string m_datasource;
    int32_t new_class_value;
    std::vector<int32_t> class_to_treath;
    std::vector<PolyVal> m_polygons;
    double buffer;


};

} // namespace pdal
