import argparse
import pdal

"""
Some useful filters combinations for complete pdal pipeline
"""


def add_radius_assign(pipeline, radius, search_3d, condition_src, condition_ref, condition_out ):
    """
    search points from "condition_src" closed from "condition_ref", and reassign them to "condition_out"
    This combination is equivalent to the CloseBy macro of TerraScan
    radius : the search distance
    search_3d : the distance reseach is in 3d if True
    condition_src, condition_ref, condition_out : a pdal condition as "Classification==2"
    """
    pipeline |= pdal.Filter.ferry(dimensions=f"=>REF_DOMAIN, =>SRS_DOMAIN, =>radius_search")
    pipeline |= pdal.Filter.assign(value=["SRS_DOMAIN = 0", f"SRS_DOMAIN = 1 WHERE {condition_src}",
                                          "REF_DOMAIN = 0", f"REF_DOMAIN = 1 WHERE {condition_ref}",
                                          "radius_search = 0"])
    pipeline |= pdal.Filter.radius_assign(radius=radius, src_domain="SRS_DOMAIN",reference_domain="REF_DOMAIN",
                                          output_dimension="radius_search", is3d=search_3d)
    pipeline |= pdal.Filter.assign(value=condition_out,where="radius_search==1")
    return pipeline



def add_grid_decimation(pipeline, grid_resolution, output_type, condition, condition_out):
    """
    Select a points in a grid  from "condition"; points not selected are reassign to "condition_out"
    This combination is equivalent to the Thin Points macro of TerraScan
    grid_resolution : resolution of the grid
    output_type : "max" or "min" (the highest or lower points of the grid)
    condition, condition_out : a pdal condition as "Classification==2"
    """
    pipeline |= pdal.Filter.ferry(dimensions=f"=>grid,")
    pipeline |= pdal.Filter.assign(value="grid = 0")
    pipeline |= pdal.Filter.grid_decimation(resolution=grid_resolution, output_name_attribute="grid",
                                            output_type=output_type, where=condition)
    pipeline |= pdal.Filter.assign(value=condition_out,where=f"grid==0 && ({condition})")
    return pipeline



def classify_hgt_ground(pipeline, hmin, hmax, condition, condition_out):
    """
       reassign points from "condition" between "hmin" and "hmax" of the ground to "condition_out"
       This combination is equivalent to the ClassifyHgtGrd macro of TerraScan
       condition, condition_out : a pdal condition as "Classification==2"
    """
    pipeline |= pdal.Filter.hag_delaunay(allow_extrapolation=True)
    condition_h = f"HeightAboveGround>{hmin} && HeightAboveGround<={hmax}"
    condition_h += " && " + condition
    pipeline |= pdal.Filter.assign(value=condition_out, where=condition_h)
    return pipeline



def keep_non_planar_pts(pipeline, condition, condition_out):
    """
       reassign points from "condition" who are planar to "condition_out"
       This combination is equivalent to the ClassifyModelKey macro of TerraScan
       condition, condition_out : a pdal condition as "Classification==2"
    """
    pipeline |= pdal.Filter.approximatecoplanar(knn=8,thresh1=25,thresh2=6,where=condition)
    pipeline |= pdal.Filter.assign(value=condition_out,where=f"Coplanar==0 && ({condition})")
    return pipeline




def build_condition(key, values):
    """
       build 'key==values[0] || key==values[1] ...'
    """
    condition = ""
    for v in values:
        condition += key+"=="+str(v)
        if v!=values[-1]:condition += " || "
    return condition

