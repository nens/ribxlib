# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import ntpath
import os

from osgeo import ogr

logger = logging.getLogger(__name__)


class ParseException(Exception):
    pass


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


def _check_filename(path):
    """Check file name.

    Folder name must be excluded.
    Extension must be present.

    """
    head, tail = ntpath.split(path)
    if head:
        msg = "folder name must be excluded: {}".format(path)
        raise Exception(msg)

    root, ext = os.path.splitext(tail)
    if ext in ['', '.']:
        msg = "file extension is missing: {}".format(tail)
        raise Exception(msg)


class Observation(object):
    """Represents the data in a ZC record, and interprets it."""
    def __init__(self, zc_node):
        self.zc_node = zc_node

    def media(self):
        """Generate the filenames mentioned. Raises ParseException if something
        is wrong with a filename."""
        for n_node in self.zc_node.xpath('N'):
            # Video fileame with an optional '|'
            path = n_node.text.split('|')[0].strip()
            _check_filename(path)
            yield path

        for m_node in self.zc_node.xpath('M'):
            # Photo filename
            path = m_node.text.strip()
            _check_filename(path)
            yield path
