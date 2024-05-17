#pragma once

#include <pdal/Filter.hpp>
#include <pdal/KDIndex.hpp>
#include <unordered_map>

extern "C" int32_t RadiusAssignFilter_ExitFunc();
extern "C" PF_ExitFunc RadiusAssignFilter_InitPlugin();

namespace pdal
{

class PDAL_DLL RadiusAssignFilter : public Filter
{
public:
    RadiusAssignFilter();
    ~RadiusAssignFilter();

    static void * create();
    static int32_t destroy(void *);
    std::string getName() const;

private:
    
    struct RadiusAssignArgs
    {
        std::string m_referenceDomain;
        std::string m_srcDomain;
        double m_radius;
        PointIdList m_ptsToUpdate;
        std::string m_outputDimension;
        Dimension::Id m_dim;
        bool search3d;
        Dimension::Id m_dim_ref, m_dim_src;
        double m_search_below, m_search_above;
    };
    std::unique_ptr<RadiusAssignArgs> m_args;
    PointViewPtr refView;
    
    virtual void addArgs(ProgramArgs& args);
    virtual void prepared(PointTableRef table);
    virtual void filter(PointView& view);
    virtual void initialize();
    virtual void addDimensions(PointLayoutPtr layout);
    virtual void ready(PointTableRef);
    
    bool doOne(PointRef& point);
    void doOneNoDomain(PointRef &point);
    
    RadiusAssignFilter& operator=(const RadiusAssignFilter&) = delete;
    RadiusAssignFilter(const RadiusAssignFilter&) = delete;
};

} // namespace pdal
