# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from datetime import datetime
import logging

from enum import Enum
from lxml import etree
from osgeo import ogr

from ribxlib import models

logger = logging.getLogger(__name__)

# NAMESPACES

NS = {
    "gml": "http://www.opengis.net/gml",
}


class Mode(Enum):
    PREINSPECTION = 1  # Ordering party -> contractor.
    INSPECTION = 2  # Contractor -> ordering party.


def parse(f, mode):
    """Parse a GWSW.Ribx / GWSW.Ribx-A document.

    GWSW.Ribx and GWSW.Ribx-A are immature standards. Their current versions
    have arguable deficiencies: a wrong use of namespaces, gml:point, etc.
    In absence of useful schema's, no attempt is made here to validate
    documents. Only information that is needed for uploadserver-site,
    is extracted and checked.

    Args:
      f (string): Full path to the file to be parsed.
      mode (Enum): See ribx.parsers.Mode.

    Returns:
      A (ribx, log) tuple. The ribxlib.models.Ribx instance carries
      the pipes, manholes and drains (to be) inspected/cleaned.
      Log is a list that contains all parsing errors.

    """
    parser = etree.XMLParser()

    try:
        tree = etree.parse(f, parser)
    except etree.XMLSyntaxError as e:
        logger.error(e)
        return models.Ribx(), _log(parser)

    # At this point, the document is well formed.

    # Even if no exception was raised, the error log might not be empty: it may
    # contain warnings, for example. TODO: should these be returned as well?

    error_log = _log(parser)

    ribx = models.Ribx()

    inspection_pipe_parser = ItemParser(
        tree, models.InspectionPipe, mode, error_log)
    cleaning_pipe_parser = ItemParser(
        tree, models.CleaningPipe, mode, error_log)
    drain_parser = ItemParser(
        tree, models.Drain, mode, error_log)
    inspection_manhole_parser = ItemParser(
        tree, models.InspectionManhole, mode, error_log)
    cleaning_manhole_parser = ItemParser(
        tree, models.CleaningManhole, mode, error_log)

    ribx.drains = drain_parser.items()
    ribx.manholes = (
        inspection_manhole_parser.items() + cleaning_manhole_parser.items())
    ribx.pipes = (
        inspection_pipe_parser.items() + cleaning_pipe_parser.items())

    return ribx, error_log


def _log(parser, level=etree.ErrorLevels.FATAL):
    """Return a list of parser errors.

    """
    return [{
        'column': error.column,
        'level': error.level_name,
        'line': error.line,
        'message': error.message,
    } for error in parser.error_log.filter_from_level(level)]


def _log2(node, expr, e, error_log):
    """Append to a list of parser errors.

    """
    message = "Element {} has problems with {}: {}".format(node.tag, expr, e)
    error_log.append({'line': node.sourceline, 'message': message})
    logger.error(message)


class ItemParser(object):
    """Parser for any kind of unit; the tags work very similarly, except
    for the different prefixes."""

    def __init__(self, tree, model, mode, error_log):
        self.tree = tree
        self.model = model
        self.mode = mode
        self.error_log = error_log

        self.expr = ''  # Keep it around so we can log it in case of error

    def tag(self, name):
        return self.model.tag[-1] + name

    def tag_value(self, node, name, complain=False):
        self.expr = self.tag(name)
        item = node.xpath(self.expr, namespaces=NS)[0]
        if not item and complain:
            raise models.ParseException(
                "Expected {} record".format(self.tag(name)))
        return item.text.strip(), item.sourceline

    def tag_point(self, node, name):
        """Interpret tag contents as gml:Point and return geom"""
        self.expr = '{}/gml:Point/gml:pos'.format(self.tag(name))
        node_set = node.xpath(self.expr, namespaces=NS)

        if node_set:
            coordinates = map(float, node_set[0].text.split())
            point = ogr.Geometry(ogr.wkbPoint)
            point.AddPoint(*coordinates)
            return point

    def items(self):
        """Return all items of the right model that are in the tree."""
        items = []

        # In inspection mode, skip everything without an inspection date.
        # ?BF must be present for something considered to be inspected!

        nodes = self.tree.xpath('//{}'.format(self.model.tag), namespaces=NS)

        for node in nodes:
            try:
                # ?AA: reference
                item_ref, item_sourceline = self.tag_value(
                    node, 'AA', complain=True)
                instance = self.model(item_ref)
                instance.sourceline = item_sourceline

                if isinstance(self.model, models.Pipe):
                    # We need two manholes and two sets of coordinates.
                    manhole1_ref, manhole1_sourceline = self.tag_value(
                        node, 'AD', complain=True)
                    instance.manhole1 = models.Manhole(manhole1_ref)
                    instance.manhole1.sourceline = manhole1_sourceline
                    instance.manhole1.geom = set.tag_point('AE')

                    manhole2_ref, manhole2_sourceline = self.tag_value(
                        node, 'AF', complain=True)
                    instance.manhole2 = models.Manhole(manhole2_ref)
                    instance.manhole2.sourceline = manhole2_sourceline
                    instance.manhole2.geom = set.tag_point('AG')

                else:
                    # ?AB holds coordinates
                    instance.geom = self.tag_point(node, 'AB')

                # ?AQ: Ownership
                instance.owner = self.tag_value(node, 'AQ')

                # ?BF: inspection date
                # Occurrence: 0 for pre-inspection?
                # Occurrence: 1 for inspection?

                node_set = node.xpath(self.tag('BF'), namespaces=NS)

                if self.mode == Mode.PREINSPECTION and len(node_set) != 0:
                    msg = "maxOccurs = 0 in {}".format(self.mode)
                    raise Exception(msg)

                if self.mode == Mode.INSPECTION and len(node_set) < 1:
                    msg = "minOccurs = 1 in {}".format(self.mode)
                    raise Exception(msg)

                if self.mode == Mode.INSPECTION and len(node_set) > 1:
                    msg = "maxOccurs = 1 in {}".format(self.mode)
                    raise Exception(msg)

                if self.mode == Mode.INSPECTION:
                    instance.inspection_date = datetime.strptime(
                        node_set[0].text.strip(),
                        "%Y-%m-%d"
                    )

                if self.model.has_video:
                    # ?BS: file name of video
                    # Occurrence: 0 for pre-inspection
                    # Occurrence: 0..1 for inspection

                    node_set = node.xpath(self.tag('BS'), namespaces=NS)

                    if self.mode == Mode.PREINSPECTION and len(node_set) != 0:
                        msg = "maxOccurs = 0 in {}".format(self.mode)
                        raise Exception(msg)

                    if self.mode == Mode.INSPECTION and len(node_set) > 1:
                        msg = "maxOccurs = 1 in {}".format(self.mode)
                        raise Exception(msg)

                    if node_set:
                        video = node_set[0].text.strip()
                        models._check_filename(video)
                        instance.media.add(video)

                # ZC: observation
                # Occurrence: 0 for pre-inspection
                # Occurrence: * for inspection
                node_set = node.xpath('ZC', namespaces=NS)

                if self.mode == Mode.PREINSPECTION and len(node_set) != 0:
                    msg = "maxOccurs = 0 in {}".format(self.mode)
                    raise Exception(msg)

                for zc_node in node_set:
                    observation = models.Observation(zc_node)
                    instance.media.update(observation.media())

                # All well...
                items.append(instance)

            except Exception as e:
                _log2(node, self.expr, e, self.error_log)

        return items
