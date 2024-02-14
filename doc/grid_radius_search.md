# filter grid decimation

Purpose
---------------------------------------------------------------------------------------------------------

The **radius search filter** add a new attribut where the value depends on their neighbors in a given radius: For each point in the domain src_domain_, if it has any neighbor with a distance lower than radius_ that belongs to the domain reference_domain_, it is updated.


Example
---------------------------------------------------------------------------------------------------------

This pipeline updates the Keypoint dimension of all points with classification 1 to 2 (unclassified and ground) that are closer than 1 meter from a point with classification 6 (building)


```
  [
     "file-input.las",
      {
          "type" : "filters.radiussearch",
          "src_domain" : "Classification[1:2]",
          "reference_domain" : "Classification[6:6]",
          "radius" : 1,
	  "output_name_attribut": "radius"
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

**update_expression** :
  A list of :ref:`assignment expressions <Assignment Expressions>` to be applied to the points that satisfy the radius search. The list of values is evaluated in order.

**output_name_attribut**: The name of the new attribut. [Default: radius]

