import tempfile
import pdal
import numpy

from pdal_ign_macro.macro import remove_dimensions


def test_remove_dimension():

    ini_las = "test/data/4_6.las"
    added_dimensions = ["DIM_1", "DIM_2"]

    tmp_las = tempfile.NamedTemporaryFile(suffix="_add.las").name

    # recuperation des données ini
    pipeline_read_ini = pdal.Pipeline() | pdal.Reader.las(ini_las)
    pipeline_read_ini.execute()
    points_ini = pipeline_read_ini.arrays[0]

    # ajout de dimensions supplémentaires
    pipeline = pdal.Pipeline()
    pipeline |= pdal.Reader.las(ini_las)
    pipeline |= pdal.Filter.ferry(dimensions="=>" + ", =>".join(added_dimensions))
    pipeline |= pdal.Writer.las(tmp_las, extra_dims="all", forward="all",)
    pipeline.execute()

    # suppression des dimensions
    remove_dimensions(tmp_las, added_dimensions, tmp_las)

    # recuperation des données finales
    pipeline_read_end = pdal.Pipeline() | pdal.Reader.las(tmp_las)
    pipeline_read_end.execute()
    points_end = pipeline_read_end.arrays[0]

    # les données ini et finales doivent être identique
    assert numpy.array_equal(points_ini, points_end)


