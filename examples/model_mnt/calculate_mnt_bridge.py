# -*- coding: utf-8 -*-
""" Calculate MNT bridge model
"""
import pdal
from pdaltools.las_info import parse_filename
from pdal_ign_macro import macro


def create_mnt_points_raster(
      input_file: str, 
      output_tiff: str,
      pixel_size: float,
      tile_width: int,
      tile_coord_scale: int,
      spatial_ref: str,
      no_data_value: int,
      ):
    """ Create MNT bridge model
    
    Args:
        input_file (str): Path to the input LAS/LAZ file
        output_tiff (str): Path to the output GeoTIFF file
        pixel_size (float): pixel size of the output raster in meters (pixels are supposed to be squares)
        tile_width (int): width of the tile in meters (used to infer the lower-left corner)
        tile_coord_scale (int): scale of the tiles coordinates in the las filename
        spatial_ref (str): spatial reference to use when reading las file
    """
    # Parameters
    _, coordX, coordY, _ = parse_filename(input_file)

    # Compute origin/number of pixels
    origin = [float(coordX) * tile_coord_scale, float(coordY) * tile_coord_scale]
    nb_pixels = [int(tile_width / pixel_size), int(tile_width / pixel_size)]

    # Create hight bridge model with PDAL
    pipeline = pdal.Pipeline()

    # Read pointcloud with PDAL
    pipeline |= pdal.Reader.las(    
            filename=input_file, 
            override_srs=spatial_ref, 
            nosrs=True
        )
    
    # Assign a classe "1" to all pointclouds except those classified  in "65"
    pipeline |= pdal.Filter.assign(
            value="Classification = 1 WHERE Classification != 65"
        )
    
    # Classify "isolated point"
    pipeline |= pdal.Filter.outlier(
            method="radius",
            min_k=10,
            radius=0.80
        )
    
    # Classify ground without outliers
    pipeline |= pdal.Filter.pmf(
            cell_size=0.2,
            ignore="Classification[7:7]",
            initial_distance=1.5,
            returns="last,only",
            max_distance=0.18,
            max_window_size=10,
            slope=0.88
        ) 
    
    # Indicates those points (classe "1") that are part of a neighborhood 
    # that is approximately coplanar (1) or not (0)
    pipeline |= pdal.Filter.approximatecoplanar(
        knn=3,
        # thresh1=5,
        # thresh2=10,
        where="Classification==1 || Classification==2"
    )

    # Keep only point clouds classified as 1 and coplanar 
    # that are close to the ground (between 0 to 60 cm height from the ground)
    pipeline =  macro.add_radius_assign(
        pipeline,
        1.5,
        False,
        condition_src="Classification==1 && Coplanar==1",
        condition_ref="Classification==2",
        condition_out="Classification=2",
        max2d_above=0.6,
        max2d_below=0,
    )

    # Save the result
    pipeline |= pdal.Writer.las(
        extra_dims="all", 
        forward="all", 
        filename="./output/point_final_knn3.las", 
        minor_version="4"
    )
    pipeline.execute()


    # # Add interpolation method
    # pipeline |= pdal.Filter.delaunay(
    #         where="classification==2"
    # )
    # pipeline |= pdal.Filter.faceraster(
    #         resolution=pixel_size,
    #         origin_x=str(origin[0] - pixel_size / 2),  # lower left corner
    #         origin_y=str(origin[1] + pixel_size / 2 - tile_width),  # lower left corner
    #         width=str(nb_pixels[0]),
    #         height=str(nb_pixels[1]),
    #     )
    
    # # Save the result
    # pipeline |= pdal.Writer.raster(
    #         filename=output_tiff,
    #         data_type="float32",
    #         nodata=no_data_value

    # )
    # pipeline.execute()

    # Save the result
    pipeline |= pdal.Writer.las(
        extra_dims="all", 
        forward="all", 
        filename="./output/point_sol_radius_assign_3.las", 
        minor_version="4"
    )
    pipeline.execute()

      