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

    @property
    def media(self):
        media = set()
        for pipe in self.pipes:
            media.update(pipe.media)
            media.update(pipe.manhole1.media)
            media.update(pipe.manhole2.media)
        for manhole in self.manholes:
            media.update(manhole.media)
        for drain in self.drains:
            media.update(drain.media)
        return media


class Pipe(object):
    """Sewerage pipe (`rioolbuis` in Dutch).

    """
    def __init__(self, ref):
        self.ref = ref
        self.manhole1 = None
        self.manhole2 = None
        self.inspection_date = None
        self.media = set()
        self.sourceline = None

    def __str__(self):
        return self.ref

    @property
    def geom(self):
        try:
            line = ogr.Geometry(ogr.wkbLineString)
            line.AddPoint(*self.manhole1.geom.GetPoint())
            line.AddPoint(*self.manhole2.geom.GetPoint())
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
        self.media = set()
        self.sourceline = None

    def __str__(self):
        return self.ref


class Drain(object):
    """A storm drain (`kolk` in Dutch).

    """
    def __init__(self, ref):
        self.ref = ref
        self.geom = None
        self.inspection_date = None
        self.media = set()
        self.sourceline = None
        self.owner = ''

    def __str__(self):
        return self.ref
