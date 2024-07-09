import pdal

"""
Some useful filters combinations for complete pdal pipeline
"""


def add_radius_assign(
    pipeline: pdal.Pipeline,
    radius: float,
    search_3d: bool,
    condition_src: str,
    condition_ref: str,
    condition_out: str,
    max2d_above: float = -1,
    max2d_below: float = -1,
) -> pdal.Pipeline:
    """
    Search points from "condition_src" that are closer than "radius_search" from points that
    belong to "condition_ref" and modify them with "condition_out"

    This combination is equivalent to the CloseBy macro of TerraScan

    Args:
        pipeline (pdal.Pipeline): pdal pipeline
        radius (float): search distance
        search_3d (bool): the distance research is in 3d if True (2d otherwise)
        condition_src (str): pdal condition for points to apply the modification to (eg. "Classification==2")
        condition_ref (str): pdal condition for the potential neighbors to search for (eg. "Classification==4")
        condition_out (str): pdal condition to apply to the points that belong to "condition_src" and
            have a point from "condition_ref" closer than "radius" (eg. "Classification==2")
        max2d_above (float, optional): In case of 2d Search, upward limit for potential neighbors. Defaults to -1.
        max2d_below (float, optional):  In case of 2d Search, downward limit for potential neighbors. Defaults to -1.

    Returns:
        pdal.Pipeline: output pipeline with the radius_assign steps added.
    """

    pipeline |= pdal.Filter.ferry(dimensions="=>REF_DOMAIN, =>SRC_DOMAIN, =>radius_search")
    pipeline |= pdal.Filter.assign(
        value=[
            "SRC_DOMAIN = 0",
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
        max2d_above=max2d_above,
        max2d_below=max2d_below,
    )
    pipeline |= pdal.Filter.assign(value=condition_out, where="radius_search==1")
    return pipeline


def classify_hgt_ground(pipeline, h_min, h_max, condition, condition_out):
    """
    reassign points from "condition" between "h_min" and "h_max" of the ground to "condition_out"
    This combination is equivalent to the ClassifyHgtGrd macro of TerraScan
    condition, condition_out : a pdal condition as "Classification==2"
    """
    pipeline |= pdal.Filter.hag_delaunay(allow_extrapolation=True)
    condition_h = f"HeightAboveGround>{h_min} && HeightAboveGround<={h_max}"
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
    condition = "("
    for v in values:
        condition += key + "==" + str(v)
        if v != values[-1]:
            condition += " || "
    condition += ")"
    return condition
