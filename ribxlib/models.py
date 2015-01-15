# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from osgeo import ogr

logger = logging.getLogger(__name__)


class Ribx(object):

    def __init__(self):
        self.pipes = []
        self.manholes = []
        self.drains = []


class Pipe(object):
    """Sewerage pipe (`rioolbuis` in Dutch).

    """
    def __init__(self, ref):
        self.ref = ref
        self.node1 = None  # Is a manhole?
        self.node2 = None  # Is a manhole?
        self.inspection_date = None

    def __str__(self):
        return self.ref

    @property
    def geom(self):
        try:
            line = ogr.Geometry(ogr.wkbLineString)
            line.AddPoint(*self.node1.geom.GetPoint())
            line.AddPoint(*self.node2.geom.GetPoint())
            return line
        except Exception as e:
            logger.error(e)


class Manhole(object):
    """A covered hole to a sewerage pipe (`put` in Dutch).

    """
    def __init__(self, ref):
        self.ref = ref
        self.geom = None
        self.inspection_date = None

    def __str__(self):
        return self.ref


class Drain(object):
    """A storm drain (`kolk` in Dutch).

    """
    def __init__(self, ref):
        self.ref = ref
        self.geom = None
        self.inspection_date = None

    def __str__(self):
        return self.ref
