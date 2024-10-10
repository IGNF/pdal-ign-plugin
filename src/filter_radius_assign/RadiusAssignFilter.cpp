#include "RadiusAssignFilter.hpp"

#include <pdal/PipelineManager.hpp>
#include <pdal/StageFactory.hpp>
#include <pdal/util/ProgramArgs.hpp>

#include <pdal/Dimension.hpp>

#include <iostream>
#include <utility>

namespace pdal
{

static PluginInfo const s_info = PluginInfo(
    "filters.radius_assign",
    "Assign some point dimension based on KNN voting",
    "" );

CREATE_SHARED_STAGE(RadiusAssignFilter, s_info)

std::string RadiusAssignFilter::getName() const { return s_info.name; }

RadiusAssignFilter::RadiusAssignFilter() :
m_args(new RadiusAssignFilter::RadiusAssignArgs)
{}


RadiusAssignFilter::~RadiusAssignFilter()
{}


void RadiusAssignFilter::addArgs(ProgramArgs& args)
{
    args.add("src_domain", "Selects which points will be subject to radius-based neighbors search", m_args->m_srcDomain, "SRC_DOMAIN");
    args.add("reference_domain", "Selects which points will be considered as potential neighbors", m_args->m_referenceDomain, "REF_DOMAIN");
    args.add("radius", "Distance of neighbors to consult", m_args->m_radius, 1.);
    args.add("output_dimension", "Name of the added dimension", m_args->m_outputDimension, "radius");
    args.add("is3d", "Search in 3d", m_args->search3d, false );
    args.add("max2d_above", "if search in 2d : upward maximum distance in Z for potential neighbors (corresponds to a search in a cylinder with a height = max2d_above above the source point). Values < 0 mean infinite height", m_args->m_max2d_above, -1.);
    args.add("max2d_below", "if search in 2d : downward maximum distance in Z for potential neighbors (corresponds to a search in a cylinder with a height = max2d_below below the source point). Values < 0 mean infinite height", m_args->m_max2d_below, -1.);
}

void RadiusAssignFilter::addDimensions(PointLayoutPtr layout)
{
    m_args->m_dim = layout->registerOrAssignDim(m_args->m_outputDimension, Dimension::Type::Unsigned8);
    m_args->m_dim_ref = layout->registerOrAssignDim(m_args->m_referenceDomain,Dimension::Type::Unsigned8);
    m_args->m_dim_src = layout->registerOrAssignDim(m_args->m_srcDomain,Dimension::Type::Unsigned8);
}

void RadiusAssignFilter::initialize()
{
    if (m_args->m_referenceDomain.empty())
        throwError("The reference_domain must be given.");
    if (m_args->m_radius <= 0)
        throwError("Invalid 'radius' option: " + std::to_string(m_args->m_radius) + ", must be > 0");
    if (m_args->m_outputDimension.empty())
        throwError("The output_dimension must be given.");
}

void RadiusAssignFilter::prepared(PointTableRef table)
{
    PointLayoutPtr layout(table.layout());
}

void RadiusAssignFilter::ready(PointTableRef)
{
    m_args->m_ptsToUpdate.clear();
}

void RadiusAssignFilter::doOneNoDomain(PointRef &point)
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
        if (m_args->m_max2d_below>=0 || m_args->m_max2d_above>=0)
        {
            bool take (true);
            for (PointId ptId : iNeighbors)
            {
                double Zpt = refView->point(ptId).getFieldAs<double>(Dimension::Id::Z);
                if (m_args->m_max2d_below>=0 && (Zref-Zpt)>m_args->m_max2d_below) {take=false; break;}
                if (m_args->m_max2d_above>=0 && (Zpt-Zref)>m_args->m_max2d_above) {take=false; break;}
            }
            if (!take) return;
        }
    }

    m_args->m_ptsToUpdate.push_back(point.pointId());
}

bool RadiusAssignFilter::doOne(PointRef& point)
{
    if (m_args->m_srcDomain.empty())  // No domain, process all points
        doOneNoDomain(point);
    else if (point.getFieldAs<int8_t>(m_args->m_dim_src)>0)
        doOneNoDomain(point);
    return true;
}

void RadiusAssignFilter::filter(PointView& view)
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

