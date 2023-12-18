/******************************************************************************
* Copyright (c) 2023, Antoine Lavenant (antoine.lavenant@ign.fr)
*
* All rights reserved.
*
****************************************************************************/

#pragma once

#include <list>
#include <memory>

#include <pdal/PointRef.hpp>
#include <pdal/Filter.hpp>
#include <pdal/Polygon.hpp>

namespace pdal
{

// keep selected points on a grid
class PDAL_DLL GridDecimationFilter : public Filter
{
public:
    GridDecimationFilter();
    ~GridDecimationFilter();

    std::string getName() const;

private:
    
    struct GridArgs
    {
        std::string m_methodKeep; // type of output (min, max)
        double m_edgeLength; // lenght of grid
        std::string m_nameAddAttribut; // name of the new attribut
        std::string m_nameWktgrid; // export wkt grid
        Dimension::Id m_dim;
    };
    
    std::unique_ptr<GridArgs> m_args;
    
    typedef std::pair<int,int> coordsGrid;
    std::map< coordsGrid, long> grid;
    
    void addArgs(ProgramArgs& args);
    virtual void initialize();

    virtual void ready(PointTableRef table);
    virtual PointViewSet run(PointViewPtr view);
    virtual void prepared(PointTableRef table);
    void addDimensions(PointLayoutPtr layout);
    
    void createGrid(BOX2D bounds);
    void processOne(BOX2D bounds, PointRef& point, PointViewPtr view);
    
    GridDecimationFilter& operator=(const GridDecimationFilter&); // not implemented
    GridDecimationFilter(const GridDecimationFilter&); // not implemented
};

} // namespace pdal
