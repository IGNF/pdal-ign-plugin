/******************************************************************************
 * Copyright (c) 2023, Antoine Lavenant (antoine.lavenant@ign.fr)
 *
 * All rights reserved.
 *
 ****************************************************************************/

#include "GridDecimationFilter.hpp"

#include <pdal/PointView.hpp>
#include <pdal/StageFactory.hpp>

#include <cstdarg>
#include <sstream>

namespace pdal {

static StaticPluginInfo const s_info{
    "filters.grid_decimation_deprecated", // better to use the pdal gridDecimation plugIN
    "keep max or min points in a grid",
    "",
};

CREATE_SHARED_STAGE(GridDecimationFilter, s_info)

std::string GridDecimationFilter::getName() const { return s_info.name; }

GridDecimationFilter::GridDecimationFilter() : m_args(new GridDecimationFilter::GridArgs) {}

GridDecimationFilter::~GridDecimationFilter() {}

void GridDecimationFilter::addArgs(ProgramArgs &args) {
  args.add("resolution", "Cell edge size, in units of X/Y", m_args->m_edgeLength, 1.);
  args.add("output_type", "Point kept into the cells ('min', 'max')", m_args->m_methodKeep, "max");
  args.add("output_dimension", "Name of the added dimension", m_args->m_nameOutDimension, "grid");
  args.add("output_wkt", "Export the grid as wkt", m_args->m_nameWktgrid, "");
}

void GridDecimationFilter::initialize() {}

void GridDecimationFilter::prepared(PointTableRef table) { PointLayoutPtr layout(table.layout()); }

void GridDecimationFilter::ready(PointTableRef table) {
  if (m_args->m_edgeLength <= 0)
    throwError("resolution must be positive.");

  if (m_args->m_methodKeep != "max" && m_args->m_methodKeep != "min")
    throwError("The output_type must be 'max' or 'min'.");

  if (m_args->m_nameOutDimension.empty())
    throwError("The output_dimension must be given.");

  if (!m_args->m_nameWktgrid.empty())
    std::remove(m_args->m_nameWktgrid.c_str());
}

void GridDecimationFilter::addDimensions(PointLayoutPtr layout) {
  m_args->m_dim =
      layout->registerOrAssignDim(m_args->m_nameOutDimension, Dimension::Type::Unsigned8);
}

void GridDecimationFilter::processOne(BOX2D bounds, PointRef &point, PointViewPtr view) {
  // get the grid cell
  double x = point.getFieldAs<double>(Dimension::Id::X);
  double y = point.getFieldAs<double>(Dimension::Id::Y);
  int id = point.getFieldAs<double>(Dimension::Id::PointId);

  // if x==(xmax of the cell), we assume the point are in the upper cell
  // if y==(ymax of the cell), we assume the point are in the right cell
  int width = static_cast<int>((x - bounds.minx) / m_args->m_edgeLength);
  int height = static_cast<int>((y - bounds.miny) / m_args->m_edgeLength);

  // to avoid numeric pb with the division (append if the point is on the grid)
  if (x < bounds.minx + width * m_args->m_edgeLength)
    width--;
  if (y < bounds.miny + height * m_args->m_edgeLength)
    height--;
  if (x >= bounds.minx + (width + 1) * m_args->m_edgeLength)
    width++;
  if (y >= bounds.miny + (height + 1) * m_args->m_edgeLength)
    height++;

  auto mptRefid = this->grid.find(std::make_pair(width, height));
  assert(mptRefid != this->grid.end());
  auto ptRefid = mptRefid->second;

  if (ptRefid == -1) {
    this->grid[std::make_pair(width, height)] = point.pointId();
    return;
  }

  PointRef ptRef = view->point(ptRefid);

  double z = point.getFieldAs<double>(Dimension::Id::Z);
  double zRef = ptRef.getFieldAs<double>(Dimension::Id::Z);

  if (this->m_args->m_methodKeep == "max" && z > zRef)
    this->grid[std::make_pair(width, height)] = point.pointId();
  if (this->m_args->m_methodKeep == "min" && z < zRef)
    this->grid[std::make_pair(width, height)] = point.pointId();
}

void GridDecimationFilter::createGrid(BOX2D bounds) {

  size_t d_width = std::floor((bounds.maxx - bounds.minx) / m_args->m_edgeLength) + 1;
  size_t d_height = std::floor((bounds.maxy - bounds.miny) / m_args->m_edgeLength) + 1;

  if (d_width < 0.0 || d_width > (std::numeric_limits<int>::max)())
    throwError("Grid width out of range.");
  if (d_height < 0.0 || d_height > (std::numeric_limits<int>::max)())
    throwError("Grid height out of range.");

  int width = static_cast<int>(d_width);
  int height = static_cast<int>(d_height);

  std::vector<Polygon> vgrid;

  for (size_t l(0); l < height; l++)
    for (size_t c(0); c < width; c++) {
      BOX2D bounds_dalle(bounds.minx + c * m_args->m_edgeLength,
                         bounds.miny + l * m_args->m_edgeLength,
                         bounds.minx + (c + 1) * m_args->m_edgeLength,
                         bounds.miny + (l + 1) * m_args->m_edgeLength);
      vgrid.push_back(Polygon(bounds_dalle));
      this->grid.insert(std::make_pair(std::make_pair(c, l), -1));
    }

  if (!m_args->m_nameWktgrid.empty()) {
    std::ofstream oss(m_args->m_nameWktgrid);
    for (auto pol : vgrid)
      oss << pol.wkt() << std::endl;
  }
}

PointViewSet GridDecimationFilter::run(PointViewPtr view) {
  if (view->empty()) {
    if (!m_args->m_nameWktgrid.empty())
      std::ofstream{m_args->m_nameWktgrid};

  } else {
    BOX2D bounds;
    view->calculateBounds(bounds);
    createGrid(bounds);

    for (PointId i = 0; i < view->size(); ++i) {
      PointRef point = view->point(i);
      processOne(bounds, point, view);
    }

    std::set<PointId> keepPoint;
    for (auto it : this->grid)
      if (it.second != -1)
        keepPoint.insert(it.second);

    for (PointId i = 0; i < view->size(); ++i) {
      PointRef point = view->point(i);
      if (keepPoint.find(view->point(i).pointId()) != keepPoint.end())
        point.setField(m_args->m_dim, int64_t(1));
      else
        point.setField(m_args->m_dim, int64_t(0));
    }
  }

  PointViewSet viewSet;
  viewSet.insert(view);
  return viewSet;
}

} // namespace pdal
