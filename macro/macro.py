import pdal

"""
Some useful filters combinations for complete pdal pipeline
"""


def add_radius_assign(pipeline, radius, search_3d, condition_src, condition_ref, condition_out):
    """
    search points from "condition_src" closed from "condition_ref", and reassign them to "condition_out"
    This combination is equivalent to the CloseBy macro of TerraScan
    radius : the search distance
    search_3d : the distance reseach is in 3d if True
    condition_src, condition_ref, condition_out : a pdal condition as "Classification==2"
    """
    pipeline |= pdal.Filter.ferry(dimensions="=>REF_DOMAIN, =>SRC_DOMAIN, =>radius_search")
    pipeline |= pdal.Filter.assign(
        value=[
            "SRS_DOMAIN = 0",
            f"SRC_DOMAIN = 1 WHERE {condition_src}",
            "REF_DOMAIN = 0",
            f"REF_DOMAIN = 1 WHERE {condition_ref}",
            "radius_search = 0",
        ]
    )
    pipeline |= pdal.Filter.radius_assign(
        radius=radius,
        src_domain="SRC_DOMAIN",
        reference_domain="REF_DOMAIN",
        output_dimension="radius_search",
        is3d=search_3d,
    )
    pipeline |= pdal.Filter.assign(value=condition_out, where="radius_search==1")
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
    pipeline |= pdal.Filter.approximatecoplanar(knn=8, thresh1=25, thresh2=6, where=condition)
    pipeline |= pdal.Filter.assign(value=condition_out, where=f"Coplanar==0 && ({condition})")
    return pipeline


def build_condition(key, values):
    """
    build 'key==values[0] || key==values[1] ...'
    """
    condition = ""
    for v in values:
        condition += key + "==" + str(v)
        if v != values[-1]:
            condition += " || "
    return condition
