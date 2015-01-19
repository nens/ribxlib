# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from osgeo import ogr
from osgeo import osr

from ribxlib.parsers import RibxParser

driver_name = "ESRI Shapefile".encode("ascii")
driver = ogr.GetDriverByName(driver_name)
datasource = driver.CreateDataSource("ribx.shp")

proj = osr.SpatialReference()
proj.SetWellKnownGeogCS(str("EPSG:28992"))
pipes_layer = datasource.CreateLayer(str('PIPES'), srs=proj)
manholes_layer = datasource.CreateLayer(str('MANHOLES'), srs=proj)

parser = RibxParser()
f = '/home/vagrant/repo/ribxlib/ribxlib/tests/data/237_0-2013-D.ribx'
parser.parse(f)

pipes = parser.pipes()
for pipe in pipes:
    print(pipe)
    dst_feature = ogr.Feature(pipes_layer.GetLayerDefn())
    dst_feature.SetGeometry(pipe.geom)
    pipes_layer.CreateFeature(dst_feature)

manholes = parser.manholes()
for manhole in manholes:
    print(manhole)
    dst_feature = ogr.Feature(manholes_layer.GetLayerDefn())
    dst_feature.SetGeometry(manhole.geom)
    manholes_layer.CreateFeature(dst_feature)

datasource.Destroy()
