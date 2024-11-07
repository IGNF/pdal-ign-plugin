# -*- coding: utf-8 -*-
""" Calculate Hight bridge model
"""
import pdal
from pdaltools.las_info import parse_filename

def create_highest_points_raster(
      input_file: str, 
      output_tiff: str,
      pixel_size: float,
      tile_width: int,
      tile_coord_scale: int,
      spatial_ref: str,
      no_data_value: int,
      ):
    """" Create hight bridge model with GridDecimation from "pdal-ign-tool"
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
    
    # The selected pointcould be the highest point on the cell
    pipeline |= pdal.Filter.gridDecimation( 
            output_type="max",
            resolution=pixel_size,
            where="Classification != 65",
            value="UserData=1",
    )
    # Add interpolation method
    pipeline |= pdal.Filter.delaunay(
            where="UserData==1"
    )
    pipeline |= pdal.Filter.faceraster(
            resolution=pixel_size,
            origin_x=str(origin[0] - pixel_size / 2),  # lower left corner
            origin_y=str(origin[1] + pixel_size / 2 - tile_width),  # lower left corner
            width=str(nb_pixels[0]),
            height=str(nb_pixels[1]),
        )
    
    # Save the result
    pipeline |= pdal.Writer.raster(
            filename=output_tiff,
            data_type="float32",
            nodata=no_data_value

    )
    pipeline.execute()


