#include "radius_searchFilter.hpp"

#include <pdal/PipelineManager.hpp>
#include <pdal/StageFactory.hpp>
#include <pdal/util/ProgramArgs.hpp>

#include <pdal/Dimension.hpp>

#include <iostream>
#include <utility>

namespace pdal
{

static PluginInfo const s_info = PluginInfo(
    "filters.radius_search",
    "Re-assign some point attributes based KNN voting",
    "" );

CREATE_SHARED_STAGE(RadiusSearchFilter, s_info)

std::string RadiusSearchFilter::getName() const { return s_info.name; }

RadiusSearchFilter::RadiusSearchFilter() :
m_args(new RadiusSearchFilter::RadiusSearchArgs)
{}


RadiusSearchFilter::~RadiusSearchFilter()
{}


void RadiusSearchFilter::addArgs(ProgramArgs& args)
{
    args.add("src_domain", "Selects which points will be subject to radius-based neighbors search", m_args->m_srcDomain, "SRC_DOMAIN");
    args.add("reference_domain", "Selects which points will be considered as potential neighbors", m_args->m_referenceDomain, "REF_DOMAIN");
    args.add("radius", "Distance of neighbors to consult", m_args->m_radius, 1.);
    args.add("output_name_attribute", "Name of the added attribut", m_args->m_nameAddAttribute, "radius" );
    args.add("search_3d", "Search in 3d", m_args->search3d, false );
    args.add("search_2d_above", "if search in 2d : filter point above the distance", m_args->m_search_bellow, 0. );
    args.add("search_2d_bellow", "if search in 2d : filter point bellow the distance", m_args->m_search_above, 0. );
}

void RadiusSearchFilter::addDimensions(PointLayoutPtr layout)
{
    m_args->m_dim = layout->registerOrAssignDim(m_args->m_nameAddAttribute, Dimension::Type::Double);
    m_args->m_dim_ref = layout->registerOrAssignDim(m_args->m_referenceDomain,Dimension::Type::Unsigned8);
    m_args->m_dim_src = layout->registerOrAssignDim(m_args->m_srcDomain,Dimension::Type::Unsigned8);
}

void RadiusSearchFilter::initialize()
{
    if (m_args->m_referenceDomain.empty())
        throwError("The reference_domain must be given.");
    if (m_args->m_radius <= 0)
        throwError("Invalid 'radius' option: " + std::to_string(m_args->m_radius) + ", must be > 0");
    if (m_args->m_nameAddAttribute.empty())
        throwError("The output_name_attribut must be given.");
}

void RadiusSearchFilter::prepared(PointTableRef table)
{
    PointLayoutPtr layout(table.layout());
}

void RadiusSearchFilter::ready(PointTableRef)
{
    m_args->m_ptsToUpdate.clear();
}

void RadiusSearchFilter::doOneNoDomain(PointRef &point)
{
    // build3dIndex and build2dIndex are build once
    PointIdList iNeighbors;
    if (m_args->search3d) iNeighbors = refView->build3dIndex().radius(point, m_args->m_radius);
    else iNeighbors = refView->build2dIndex().radius(point, m_args->m_radius);
    
    if (iNeighbors.size() == 0)
        return;
    
    if (!m_args->search3d)
    {
        double Zref = point.getFieldAs<double>(Dimension::Id::Z);
        if (m_args->m_search_bellow>0 || m_args->m_search_above>0)
        {
            bool take (false);
            for (PointId ptId : iNeighbors)
            {
                double Zpt = refView->point(ptId).getFieldAs<double>(Dimension::Id::Z);
                if (m_args->m_search_bellow>0 && Zpt>Zref && (Zpt-Zref)<m_args->m_search_bellow) {take=true; break;}
                if (m_args->m_search_above>0 && Zpt<Zref && (Zref-Zpt)<m_args->m_search_above) {take=true; break;}
            }
            if (!take) return;
        }
    }
    
    m_args->m_ptsToUpdate.push_back(point.pointId());
}


// update point.  kdi and temp both reference the NN point cloud
bool RadiusSearchFilter::doOne(PointRef& point)
{
    if (m_args->m_srcDomain.empty())  // No domain, process all points
        doOneNoDomain(point);
    else if (point.getFieldAs<int8_t>(m_args->m_dim_src)>0)
        doOneNoDomain(point);
    return true;
}

void RadiusSearchFilter::filter(PointView& view)
{
    PointRef point_src(view, 0);
    PointRef temp(view, 0);
    
    refView = view.makeNew();
    for (PointId id = 0; id < view.size(); ++id)
    {
        temp.setPointId(id);
        temp.setField(m_args->m_dim, int64_t(0)); // initialisation
        
        // process only points that satisfy a domain condition
        if (temp.getFieldAs<int8_t>(m_args->m_dim_ref)>0)
            refView->appendPoint(view, id);
    }
        
    for (PointId id = 0; id < view.size(); ++id)
    {
        point_src.setPointId(id);
        doOne(point_src);
    }
    for (auto id: m_args->m_ptsToUpdate)
    {
        temp.setPointId(id);
        temp.setField(m_args->m_dim, int64_t(1));
    }
}

} // namespace pdal

