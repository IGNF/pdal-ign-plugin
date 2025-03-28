#include "ClassifyByDistanceFilter.hpp"

#include <pdal/PipelineManager.hpp>
#include <pdal/StageFactory.hpp>
#include <pdal/util/ProgramArgs.hpp>

#include <pdal/Dimension.hpp>

#include <iostream>
#include <utility>

namespace pdal
{

static PluginInfo const s_info = PluginInfo(
    "filters.classify_by_distance",
    "assign a new value for points whose distance from another class is less than a given distance",
    "" );

CREATE_SHARED_STAGE(ClassifyByDistanceFilter, s_info)

std::string ClassifyByDistanceFilter::getName() const { return s_info.name; }

ClassifyByDistanceFilter::ClassifyByDistanceFilter() :
m_args(new ClassifyByDistanceFilter::ClassifyByDistanceArgs)
{}


ClassifyByDistanceFilter::~ClassifyByDistanceFilter()
{}


void ClassifyByDistanceFilter::addArgs(ProgramArgs& args)
{
    args.add("src_domain", "Classification of points which will be subject to new classification", m_args->m_srcDomain, 0);
    args.add("reference_domain", "Classification of points which will be considered for the distance search", m_args->m_referenceDomain, 1);
    args.add("distance_min", "distance max for new classification", m_args->distance_min, 0.);
    args.add("distance_max", "distance max for new classification", m_args->distance_max, 0.);
    args.add("new_class_value", "New classification value", m_args->new_class_value, 100);
    args.add("only_bellow", "Only points above", m_args->only_above, false);
}

void ClassifyByDistanceFilter::filter(PointView& view)
{
    PointRef point_src(view, 0);
    PointRef temp(view, 0);

    refView = view.makeNew();
    for (PointId id = 0; id < view.size(); ++id)
    {
        uint8_t classif = view.getFieldAs<uint8_t>(Dimension::Id::Classification, id);
        if (classif == m_args->m_referenceDomain)
            refView->appendPoint(view, id);
    }
    if (!refView->size()) return;
    KD3Index& index = refView->build3dIndex();
    
    size_t k = 1;  // only one point - the closest
    for (PointId idx = 0; idx < view.size(); ++idx)
    {
        uint8_t classif = view.getFieldAs<uint8_t>(Dimension::Id::Classification, idx);
        if (classif != m_args->m_srcDomain) continue;
                
        PointIdList indices(k);
        std::vector<double> sqr_dists(k);
        
        double x = view.getFieldAs<double>(Dimension::Id::X, idx);
        double y = view.getFieldAs<double>(Dimension::Id::Y, idx);
        double z = view.getFieldAs<double>(Dimension::Id::Z, idx);
        index.knnSearch(x, y, z, k, &indices, &sqr_dists);

        double val = std::sqrt(sqr_dists[k - 1]);
        if (val > m_args->distance_min && val < m_args->distance_max)
        {
            if (m_args->only_above){
                double z_nei = refView->getFieldAs<double>(Dimension::Id::Z, indices[0]);
                if ( z_nei < z ) continue;
            }
            
            view.setField(Dimension::Id::Classification, idx, m_args->new_class_value);
        }
    }
}

} // namespace pdal

