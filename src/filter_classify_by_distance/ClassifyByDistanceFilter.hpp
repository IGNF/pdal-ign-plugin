#pragma once

#include <pdal/Filter.hpp>
#include <pdal/KDIndex.hpp>
#include <unordered_map>

namespace pdal
{

class PDAL_DLL ClassifyByDistanceFilter : public Filter
{
public:
    ClassifyByDistanceFilter();
    ~ClassifyByDistanceFilter();

    static void * create();
    static int32_t destroy(void *);
    std::string getName() const;

private:
    
    struct ClassifyByDistanceArgs
    {
        int m_referenceDomain;
        int m_srcDomain;
        int new_class_value;
        double distance_min;
        double distance_max;
        bool only_above;
    };
    std::unique_ptr<ClassifyByDistanceArgs> m_args;
    PointViewPtr refView;
    
    virtual void addArgs(ProgramArgs& args);
    virtual void filter(PointView& view);
    
    size_t m_k;
};

} // namespace pdal
