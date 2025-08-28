
### 0.5.5

- update mark_points_to_use_for_digital_models_with_new_dimension to handle points with classification 68

### 0.5.4

- update ign-pdal-tools to 1.12.3 in Docker.pdal (fix add_points_in_pointcloud: crs format consistency)


### 0.5.3

- update ign-pdal-tools to 1.12.3 (fix add_points_in_pointcloud: crs format consistency)

### 0.5.2

- update ign-pdal-tools to 1.12.2 (fix las2las use in standardize_format)

### 0.5.1

- update ign-pdal-tools to 1.12.0 (fix "add virtual points" when there is no point to add)

## 0.5.0

- Update to ign-pdal-tools 1.11.1 for fix in add_points_in_pointcloud
- Add Dockerfile.pdal for use non official version of pdal
- fix tests to next version of pdal

### 0.4.1

- In preprocessing_mnx, add ability to add virtual points from lines geometry file (ign-pdal-tools 1.8.1)

## 0.4.0

- Add preprocessing_mnx script, that adds points from a geojson + mark points for dsm/dtm
- Add example to run a local python script in the pdal_ign_plugin docker image

### 0.3.1

- improve code readability in the radius_assign filter (Z limits part).
- fix the script for MNx pre-processing (Z limits were inverted)
- improve tests and test data

## 0.3.0

Update algorithm of [mark_points_to_use_for_digital_models_with_new_dimension](pdal_ign_macro/mark_points_to_use_for_digital_models_with_new_dimension.py)
In details :
- manage water and virtuals points,
- update building consideration
- 2 levels of water

### 0.2.1

Fix (and test) arguments parsing in [mark_points_to_use_for_digital_models_with_new_dimension](pdal_ign_macro/mark_points_to_use_for_digital_models_with_new_dimension.py)

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
