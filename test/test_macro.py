import tempfile

import pdal

from pdal_ign_macro import macro


def test_classify_hgt_ground():

    input_las = "test/data/4_6.las"
    Zmax_2 = 7100
    Hmin = -0.5
    Hmax = 10

    with tempfile.NamedTemporaryFile(suffix="_out.las") as output_las:

        pipeline = pdal.Pipeline() | pdal.Reader.las(input_las)
        macro.classify_hgt_ground(
            pipeline, Hmin, Hmax, condition="Classification==1", assignment_out="Classification=3"
        )
        pipeline |= pdal.Writer.las(
            extra_dims="all", forward="all", filename=output_las.name, minor_version="4"
        )

        pipeline.execute()
        arrays = pipeline.arrays
        array = arrays[0]

        nb_pts_inside = 0
        for pt in array:
            if pt["Classification"] == 3:
                nb_pts_inside += 1
                assert pt["Z"] < Zmax_2 + Hmax

        assert nb_pts_inside > 0


def test_classify_hgt_ground_list():

    input_las = "test/data/4_7.las"

    Zmax_2_3 = 7110
    Hmin = -0.5
    Hmax = 10

    with tempfile.NamedTemporaryFile(suffix="_out.las") as output_las:

        pipeline = pdal.Pipeline() | pdal.Reader.las(input_las)
        macro.classify_hgt_ground_list(
            pipeline,
            [2, 3],
            Hmin,
            Hmax,
            condition="Classification==1",
            assignment_out="Classification=4",
        )
        pipeline |= pdal.Writer.las(
            extra_dims="all", forward="all", filename=output_las.name, minor_version="4"
        )

        pipeline.execute()
        arrays = pipeline.arrays
        array = arrays[0]

        nb_pts_inside = 0
        for pt in array:
            if pt["Classification"] == 4:
                nb_pts_inside += 1
                assert pt["Z"] < Zmax_2_3 + Hmax

        assert nb_pts_inside > 0


def test_classify_thin_grid_2d():

    input_las = "test/data/4_6.las"
    grid_size = 5

    with tempfile.NamedTemporaryFile(suffix="_out.las") as output_las:

        pipeline = pdal.Pipeline() | pdal.Reader.las(input_las)
        macro.classify_thin_grid_2d(
            pipeline,
            condition="Classification==1",
            assignment_out="Classification=3",
            grid_size=grid_size,
            mode="max",
        )
        pipeline |= pdal.Writer.las(
            extra_dims="all", forward="all", filename=output_las.name, minor_version="4"
        )

        pipeline.execute()
        arrays = pipeline.arrays
        array = arrays[0]

        nb_pts_inside = 0
        for pt in array:
            if pt["Classification"] == 3:
                nb_pts_inside += 1

        assert nb_pts_inside > 0
