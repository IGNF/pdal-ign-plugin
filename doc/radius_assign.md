# filter radius assign

Purpose
---------------------------------------------------------------------------------------------------------

The **radius assign filter** add a new attribut where the value depends on their neighbors in a given radius: For each point in the domain src_domain_, if it has any neighbor with a distance lower than radius_ that belongs to the domain reference_domain_, it is updated.


Example
---------------------------------------------------------------------------------------------------------

This pipeline updates the Keypoint dimension of all points with classification 1 to 2 (unclassified and ground) that are closer than 1 meter from a point with classification 6 (building)


```
  [
     "file-input.las",
      {
          "type" : "filters.radius_assign",
          "src_domain" : "Classification[1:2]",
          "reference_domain" : "Classification[6:6]",
          "radius" : 1,
	  	  "output_dimension": "radius",
	  	  "is3d": True
      },
      "output.las"
  ]
```

Options
---------------------------------------------------------------------------------------------------------------------------------------------------------------------

**src_domain** :
  A :ref:`range <ranges>` which selects points to be processed by the filter. Can be specified multiple times.  Points satisfying any range will be processed

**reference_domain** :
  A :ref:`range <ranges>` which selects points that can are considered as potential neighbors. Can be specified multiple times.

**radius** :
  An positive float which specifies the radius for the neighbors search.

**output_dimension**: The name of the new dimension'. [Default: radius]

**is3d**: Search in 3d (as a ball). [Default: false]

**is2d_above**: If search in 2d : upward maximum distance in Z for potential neighbors (corresponds to a search in a cylinder with a height = is2d_above above the source point). Default (0) = infinite height [Default: 0.]

**is2d_below**: If search in 2d : upward maximum distance in Z for potential neighbors (corresponds to a search in a cylinder with a height = is2d_below below the source point). Default (0) = infinite height [Default: 0.]
