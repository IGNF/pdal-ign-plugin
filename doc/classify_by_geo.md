# filter classify by geo

Purpose
---------------------------------------------------------------------------------------------------------

The **classify by geo filter** apply a classification values for points who are included inside polygons from a geometric file

Example
---------------------------------------------------------------------------------------------------------

This pipeline updates the classification to 66 of all points who are included inside the geometry included in the file_geo.geojson


```
  [
     "file-input.las",
      {
          "type" : "filters.classify_by_geo",
          "datasource" : /.../file_geo.geojson,
          "new_class_value" : 66,
      },
      "output.las"
  ]
```

Options
---------------------------------------------------------------------------------------------------------------------------------------------------------------------

**datasource** :
  The file source of the geometric polygons or multipolygons.

**new_class_value** :
  The classification value apply to points who are inside geometry
