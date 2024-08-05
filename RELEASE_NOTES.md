## 0.2.0
- Update algorithm for DxM marking in [mark_points_to_use_for_digital_models_with_new_dimension](pdal_ign_macro/mark_points_to_use_for_digital_models_with_new_dimension.py)
- Add a temporary buffer on the las input to prevent side effects on tile borders
- Remove temporary extra dimensions added during points marking

### 0.1.1

Fix arguments that are passed from argparse to the main function

## 0.1.0

Contains 2 pdal filters:
- radius_assign
- grid_decimation_deprecated (contains fixes that are not implemented in the pdal GridDecimation filter as of 2024-06)

Contains python macros in [macro.py](macro/macro.py):
- add_radius_assign (to apply radius assign with conditions) with 3d radius, 2d radius and 2d radius with upper/lower bounds in Z
- classify_hgt_ground
- keep_non_planar_pts

Contains a python script for DSM/DTM points selection: [mark_points_to_use_for_digital_models_with_new_dimension.py](scripts/mark_points_to_use_for_digital_models_with_new_dimension.py)
