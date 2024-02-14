#pragma once

#include <pdal/Filter.hpp>
#include <pdal/KDIndex.hpp>
#include <unordered_map>

extern "C" int32_t RadiusSearchFilter_ExitFunc();
extern "C" PF_ExitFunc RadiusSearchFilter_InitPlugin();

namespace pdal
{

class PDAL_DLL RadiusSearchFilter : public Filter
{
public:
    RadiusSearchFilter();
    ~RadiusSearchFilter();

    static void * create();
    static int32_t destroy(void *);
    std::string getName() const;

private:
    
    struct RadiusSearchArgs
    {
        std::string m_referenceDomain;
        std::string m_srcDomain;
        double m_radius;
        PointIdList m_ptsToUpdate;
        std::string m_nameAddAttribute;
        Dimension::Id m_dim;
        bool search3d;
        Dimension::Id m_dim_ref, m_dim_src;
    };
    std::unique_ptr<RadiusSearchArgs> m_args;
    PointViewPtr refView;
    
    virtual void addArgs(ProgramArgs& args);
    virtual void prepared(PointTableRef table);
    virtual void filter(PointView& view);
    virtual void initialize();
    virtual void addDimensions(PointLayoutPtr layout);
    virtual void ready(PointTableRef);
    
    bool doOne(PointRef& point);
    void doOneNoDomain(PointRef &point);
    
    RadiusSearchFilter& operator=(const RadiusSearchFilter&) = delete;
    RadiusSearchFilter(const RadiusSearchFilter&) = delete;
};

} // namespace pdal
