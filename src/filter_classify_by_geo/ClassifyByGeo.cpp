#include "ClassifyByGeo.hpp"

#include <vector>

#include <ogr_api.h>

#include <pdal/Polygon.hpp>
#include <pdal/util/ProgramArgs.hpp>
#include <pdal/private/gdal/GDALUtils.hpp>
#include <pdal/private/gdal/SpatialRef.hpp>

namespace pdal
{

static StaticPluginInfo const s_info
{
    "filters.classify_by_geo",
    "Assign Classification for points inside geometry.",
    ""
};

CREATE_STATIC_STAGE(ClassifyByGeoFilter, s_info)

void ClassifyByGeoFilter::addArgs(ProgramArgs& args)
{
    args.add("new_class_value", "Dimension on which to filter", new_class_value).setPositional();
    args.add("datasource", "OGR-readable datasource for Polygon or Multipolygon data", m_datasource).setPositional();
}

void ClassifyByGeoFilter::initialize()
{
    gdal::registerDrivers();
}

void ClassifyByGeoFilter::ready(PointTableRef table)
{
    OGRDSPtr m_ds = OGRDSPtr(OGROpen(m_datasource.c_str(), 0, 0),
            [](void *p){ if (p) ::OGR_DS_Destroy(p); });
    if (!m_ds)
        throwError("Unable to open data source '" + m_datasource + "'");

    OGRLayerH m_lyr = OGR_DS_GetLayer(m_ds.get(), 0);

    auto featureDeleter = [](void *p)
    {
        if (p)
            ::OGR_F_Destroy(p);
    };
    OGRFeaturePtr feature = OGRFeaturePtr(OGR_L_GetNextFeature(m_lyr), featureDeleter);
    
    do
    {
        OGRGeometryH geom = OGR_F_GetGeometryRef(feature.get());

        m_polygons.push_back(
            { Polygon(geom), new_class_value} );

        feature = OGRFeaturePtr(OGR_L_GetNextFeature(m_lyr), featureDeleter);
    }
    while (feature);

    // Initialise m_grids, otherwise this will lead to a race condition when
    // using threading.
    for (const auto& poly : m_polygons)
    {
        poly.geom.initGrids();
    }
}

bool ClassifyByGeoFilter::processOne(PointRef& point)
{
    for (const auto& poly : m_polygons)
    {
        double x = point.getFieldAs<double>(Dimension::Id::X);
        double y = point.getFieldAs<double>(Dimension::Id::Y);
        if (poly.geom.contains(x, y))
        {
            point.setField(Dimension::Id::Classification, poly.val);
        }
    }
    return true;
}

PointViewSet ClassifyByGeoFilter::run(PointViewPtr view)
{
    for (PointId id = 0; id < view->size(); ++id)
    {
        PointRef point = view->point(id);
        processOne(point);
    }
    
    PointViewSet viewSet;
    viewSet.insert(view);
    return viewSet;
}

} // namespace pdal
