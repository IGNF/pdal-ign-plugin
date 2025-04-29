# filter classify by distance

Purpose
---------------------------------------------------------------------------------------------------------

The **classify by distance filter** apply a classification values for points whose distance from another class is less than a given distance

Example
---------------------------------------------------------------------------------------------------------

This pipeline updates the classification dimension of all points with classification 1 to 3 that are closer than 10 meter from a point with classification 2


```
  [
     "file-input.las",
      {
          "type" : "filters.classify_by_geo",
          "distance": 10,
          "src_domain": 1,
          "reference_domain": 2,
          "new_class_value": 3,
      },
      "output.las"
  ]
```

Options
---------------------------------------------------------------------------------------------------------------------------------------------------------------------

**distance** :
  The test distance.

**src_domain** :
  The points who will be transformed

**reference_domain** :
  The reference points

**new_class_value** :
  The classification value apply to points who transformed
