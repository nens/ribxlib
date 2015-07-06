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


class Thing(object):
    """Common superclass for the various kinds of things. The more we
    can put in here, the better."""
    has_video = False

    def __init__(self, ref):
        self.ref = ref
        self.inspection_date = None
        self.media = set()
        self.sourceline = None
        self.work_impossible = None  # If it was, this holds the reason

    @classmethod
    def xd_explanation(self, xd):
        return xd


class Pipe(Thing):
    """Sewerage pipe (`rioolbuis` in Dutch).

    """
    has_video = True

    def __init__(self, ref):
        super(Pipe, self).__init__(ref)
        self.manhole1 = None
        self.manhole2 = None

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

    @classmethod
    def xd_explanation(self, xd):
        # Taken from the modelbeschrijving PDF page 41, see
        # ribxlib/doc.
        return {
            'A': 'Voertuig/obstakel op toegang',
            'B': 'Straat niet toegankelijk voor het voertuig',
            'Z': 'Andere reden.'
        }.get(xd, 'Onbekende xXD code {}'.format(xd))


class InspectionPipe(Pipe):
    tag = 'ZB_A'


class CleaningPipe(Pipe):
    tag = 'ZB_G'


class Manhole(Thing):
    """A covered hole to a sewerage pipe (`put` in Dutch).

    """
    has_video = True

    def __init__(self, ref):
        super(Manhole, self).__init__(ref)
        self.geom = None

    def __str__(self):
        return self.ref

    @classmethod
    def xd_explanation(self, xd):
        # Taken from the modelbeschrijving PDF page 46, see
        # ribxlib/doc.
        return {
            'A': 'Voertuig/obstakel op toegang',
            'B': 'Straat niet toegankelijk voor het voertuig',
            'C': 'Groen blokkeert de toegang',
            'D': 'Niet aangetroffen',
            'E': 'Deksel vast',
            'Z': 'Andere reden.'
        }.get(xd, 'Onbekende xXD code {}'.format(xd))


class InspectionManhole(Manhole):
    tag = 'ZB_C'


class CleaningManhole(Manhole):
    tag = 'ZB_J'


class Drain(Thing):
    """A storm drain (`kolk` in Dutch).

    """
    tag = 'ZB_E'

    def __init__(self, ref):
        super(Drain, self).__init__(ref)
        self.geom = None
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
