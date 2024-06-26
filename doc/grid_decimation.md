# filter grid decimation

**Deprecated** : *better use the gridDecimation filter of pdal > 2.7*

Purpose
---------------------------------------------------------------------------------------------------------

The **grid decimation filter** transform only one point in each cells of a grid calculated from the points cloud and a resolution therm. The transformation is done by the value information. The selected point could be the highest or the lowest point on the cell. It can be used, for exemple, to quickly filter vegetation points in order to keep only the canopy points. A new dimension is created with the value '1' for the grid, and '0' for the other points.


Example
---------------------------------------------------------------------------------------------------------

This example transform highest points of classification 5 in classification 9, on a grid of 0.75m square. 


```
  [
     "file-input.las",
    {
        "type": "filters.gridDecimation",
	"output_type":"max",
        "output_dimension": "grid",
	"output_wkt":"file-output.wkt"
    },
    {
          "type":"writers.las",
          "filename":"file-output.las"
    }
  ]
```

Options
---------------------------------------------------------------------------------------------------------------------------------------------------------------------

**output_type** : 
  The type of points transform by the value information. The value should be ``"max"`` for transform the highest point, or ``"min"`` for the lowest. [Default: false]

**resolution** :
  The resolution of the cells in meter. [Default: 1.]

**output_dimension**: The name of the new dimension. [Default: grid]

**output_wkt**: the name of the export grid file as wkt polygon. If none, no export [Default:""]
