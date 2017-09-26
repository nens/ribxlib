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
        self.inspection_pipes = []
        self.cleaning_pipes = []
        self.inspection_manholes = []
        self.cleaning_manholes = []
        self.drains = []

    @property
    def media(self):
        """Combine the media sets of all elements in this RIBX."""
        media = set()
        for pipe in self.inspection_pipes + self.cleaning_pipes:
            media.update(pipe.media)
            media.update(pipe.manhole1.media)
            media.update(pipe.manhole2.media)
        for manhole in self.inspection_manholes + self.cleaning_manholes:
            media.update(manhole.media)
        for drain in self.drains:
            media.update(drain.media)
        return media


class SewerElement(object):
    """Common superclass for pipes, drains and manholes. The more we
    can put in here, the better."""
    # According to the spec, not everything can have the video
    # tag. Subclasses that can set this to True.
    has_video = False

    def __init__(self, ref):
        # Code of this element
        self.ref = ref

        # Stays empty if file is used to describe the work to be done, must be
        # filled in if the work was done (or turned out not to be possible).
        self.inspection_date = None

        # A set of related filenames that will be uploaded later.
        self.media = set()

        # Line in the RIBX file where this element's node started.
        self.sourceline = None

        # Sometimes it was impossible to do the work, if so then this element
        # will contain the reason as a string.
        self.work_impossible = None

        # True if a '*XC' tag was used ("ontbreekt in opdracht")
        self.new = False

    def print_for_debug(self):
        print(self.ref)
        print('-' * len(self.ref))
        print('')
        print('Inspection date: %s' % self.inspection_date)
        print('Number of expected media files: %s' % len(self.media))


class Pipe(SewerElement):
    """Sewerage pipe (`rioolbuis` in Dutch).

    """
    has_video = True

    def __init__(self, ref):
        super(Pipe, self).__init__(ref)
        self.manhole1 = None
        self.manhole2 = None
        # We're explicitly interested in angle observations ('hellingmeting')
        self.angle_observations = []

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

    def print_for_debug(self):
        super(Pipe, self).print_for_debug()
        print("From manhole %s to manhole %s" % (self.manhole1, self.manhole2))
        if self.angle_observations:
            print("%s angle observations" % len(self.angle_observations))
            for angle_observation in self.angle_observations:
                print("    %.02f" % angle_observation.lengthwise_location)


class InspectionPipe(Pipe):
    tag = 'ZB_A'

    def __init__(self, ref):
        super(InspectionPipe, self).__init__(ref)
        self.manhole_start = None  # The starting manhole of the inspection


class CleaningPipe(Pipe):
    tag = 'ZB_G'


class Manhole(SewerElement):
    """A covered hole to a sewerage pipe (`put` in Dutch).

    """
    has_video = True

    def __init__(self, ref):
        super(Manhole, self).__init__(ref)
        self.geom = None

    def __str__(self):
        return self.ref


class InspectionManhole(Manhole):
    tag = 'ZB_C'


class CleaningManhole(Manhole):
    tag = 'ZB_J'


class Drain(SewerElement):
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


class AngleObservation(Observation):

    def __init__(self, zc_node):
        super(AngleObservation, self).__init__(zc_node)
        self.lengthwise_location = float(zc_node.xpath('I')[0].text.strip())
