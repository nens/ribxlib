# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from datetime import datetime
import logging
import ntpath
import os

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
    ribx.pipes = _pipes(tree, mode, error_log)
    ribx.manholes = _manholes(tree, mode, error_log)
    ribx.drains = _drains(tree, mode, error_log)

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


def _pipes(tree, mode, error_log):
    """Return a list of pipes.

    """
    pipes = []

    expr = '//ZB_A|ZB_G'

    nodes = tree.xpath(expr, namespaces=NS)

    for node in nodes:

        try:

            # AAA (inspection) or GAA (cleaning): pipe reference
            # Occurrence: 1

            expr = 'AAA|GAA'
            item = node.xpath(expr, namespaces=NS)
            if not item:
                raise models.ParseException(
                    "Expected AAA or GAA in pipe record")
            item = item[0]
            pipe_ref = item.text.strip()
            pipe = models.Pipe(pipe_ref)
            pipe.sourceline = item.sourceline

            # AAD (inspection) or GAD (cleaning) : manhole1 reference
            # Occurrence: 1

            expr = 'AAD|GAD'
            item = node.xpath(expr, namespaces=NS)
            if not item:
                raise models.ParseException(
                    "Expected AAD or GAD in pipe record")
            item = item[0]
            manhole1_ref = item.text.strip()
            manhole1 = models.Manhole(manhole1_ref)
            manhole1.sourceline = item.sourceline
            pipe.manhole1 = manhole1

            # AAF (inspection) or GAF (cleaning): manhole2 reference
            # Occurrence: 1

            expr = 'AAF|GAF'
            item = node.xpath(expr, namespaces=NS)
            if not item:
                raise models.ParseException(
                    "Expected AAF or GAF in pipe record")
            item = item[0]
            manhole2_ref = item.text.strip()
            manhole2 = models.Manhole(manhole2_ref)
            manhole2.sourceline = item.sourceline
            pipe.manhole2 = manhole2

            # AAE: manhole1 coordinates
            # Occurrence: 0..1
            # gml:coordinates is deprecated in favour of gml:pos
            # The spec uses gml:point? gml:Point is correct!

            expr = 'AAE/gml:Point/gml:pos'
            node_set = node.xpath(expr, namespaces=NS)
            if not node_set:
                expr = 'GAE/gml:Point/gml:pos'
                node_set = node.xpath(expr, namespaces=NS)

            if node_set:
                coordinates = map(float, node_set[0].text.split())
                point = ogr.Geometry(ogr.wkbPoint)
                point.AddPoint(*coordinates)
                pipe.manhole1.geom = point

            # AAG: manhole2 coordinates
            # Occurrence: 0..1

            expr = 'AAG/gml:Point/gml:pos'
            node_set = node.xpath(expr, namespaces=NS)
            if not node_set:
                expr = 'GAG/gml:Point/gml:pos'
                node_set = node.xpath(expr, namespaces=NS)

            if node_set:
                coordinates = map(float, node_set[0].text.split())
                point = ogr.Geometry(ogr.wkbPoint)
                point.AddPoint(*coordinates)
                pipe.manhole2.geom = point

            # ABF: inspection date
            # Occurrence: 0 for pre-inspection
            # Occurrence: 1 for inspection

            expr = 'ABF|GBF'
            node_set = node.xpath(expr, namespaces=NS)

            if mode == Mode.PREINSPECTION and len(node_set) != 0:
                msg = "maxOccurs = 0 in {}".format(mode)
                raise Exception(msg)

            if mode == Mode.INSPECTION and len(node_set) < 1:
                msg = "minOccurs = 1 in {}".format(mode)
                raise Exception(msg)

            if mode == Mode.INSPECTION and len(node_set) > 1:
                msg = "maxOccurs = 1 in {}".format(mode)
                raise Exception(msg)

            if mode == Mode.INSPECTION:
                pipe.inspection_date = datetime.strptime(
                    node_set[0].text.strip(),
                    "%Y-%m-%d"
                )

            # ABS: file name of video
            # Occurrence: 0 for pre-inspection
            # Occurrence: 0..1 for inspection

            expr = 'ABS|GBS'
            node_set = node.xpath(expr, namespaces=NS)

            if mode == Mode.PREINSPECTION and len(node_set) != 0:
                msg = "maxOccurs = 0 in {}".format(mode)
                raise Exception(msg)

            if mode == Mode.INSPECTION and len(node_set) > 1:
                msg = "maxOccurs = 1 in {}".format(mode)
                raise Exception(msg)

            if node_set:
                video = node_set[0].text.strip()
                models._check_filename(video)
                pipe.media.add(video)

            # ZC: observation
            # Occurrence: 0 for pre-inspection
            # Occurrence: * for inspection
            expr = 'ZC'
            node_set = node.xpath(expr, namespaces=NS)

            if mode == Mode.PREINSPECTION and len(node_set) != 0:
                msg = "maxOccurs = 0 in {}".format(mode)
                raise models.ParseException(msg)

            for zc_node in node_set:
                observation = models.Observation(zc_node)
                pipe.media.update(observation.media())

            # All well...
            pipes.append(pipe)

        except Exception as e:
            _log2(node, expr, e, error_log)

    return pipes


def _manholes(tree, mode, error_log):
    """Return a list of manholes.

    """
    manholes = []

    # In inspection mode, skip all manholes without an inspection date.
    # CBF must be present for a manhole considered to be inspected!

    expr = '//ZB_C|ZB_J'
    nodes = tree.xpath(expr, namespaces=NS)

    for node in nodes:

        try:

            # CAA: manhole reference

            expr = 'CAA|JAA'
            item = node.xpath(expr, namespaces=NS)[0]
            manhole_ref = item.text.strip()
            manhole = models.Manhole(manhole_ref)
            manhole.sourceline = item.sourceline

            # CAB: manhole coordinates
            # Occurrence: 0..1
            # gml:coordinates is deprecated in favour of gml:pos
            # The spec uses gml:point? gml:Point is correct!

            expr = 'CAB/gml:Point/gml:pos'
            node_set = node.xpath(expr, namespaces=NS)
            if not node_set:
                expr = 'JAB/gml:Point/gml:pos'
                node_set = node.xpath(expr, namespaces=NS)

            if node_set:
                coordinates = map(float, node_set[0].text.split())
                point = ogr.Geometry(ogr.wkbPoint)
                point.AddPoint(*coordinates)
                manhole.geom = point

            # CBF: inspection date
            # Occurrence: 0 for pre-inspection
            # Occurrence: 1 for inspection

            expr = 'CBF|JBF'
            node_set = node.xpath(expr, namespaces=NS)

            if mode == Mode.PREINSPECTION and len(node_set) != 0:
                msg = "maxOccurs = 0 in {}".format(mode)
                raise Exception(msg)

            if mode == Mode.INSPECTION and len(node_set) < 1:
                msg = "minOccurs = 1 in {}".format(mode)
                raise Exception(msg)

            if mode == Mode.INSPECTION and len(node_set) > 1:
                msg = "maxOccurs = 1 in {}".format(mode)
                raise Exception(msg)

            if mode == Mode.INSPECTION:
                manhole.inspection_date = datetime.strptime(
                    node_set[0].text.strip(),
                    "%Y-%m-%d"
                )

            # CBS: file name of video
            # Occurrence: 0 for pre-inspection
            # Occurrence: 0..1 for inspection

            expr = 'CBS|JBS'
            node_set = node.xpath(expr, namespaces=NS)

            if mode == Mode.PREINSPECTION and len(node_set) != 0:
                msg = "maxOccurs = 0 in {}".format(mode)
                raise Exception(msg)

            if mode == Mode.INSPECTION and len(node_set) > 1:
                msg = "maxOccurs = 1 in {}".format(mode)
                raise Exception(msg)

            if node_set:
                video = node_set[0].text.strip()
                models._check_filename(video)
                manhole.media.add(video)

            # ZC: observation
            # Occurrence: 0 for pre-inspection
            # Occurrence: * for inspection
            expr = 'ZC'
            node_set = node.xpath(expr, namespaces=NS)

            if mode == Mode.PREINSPECTION and len(node_set) != 0:
                msg = "maxOccurs = 0 in {}".format(mode)
                raise models.ParseException(msg)

            for zc_node in node_set:
                observation = models.Observation(zc_node)
                manhole.media.update(observation.media())

            # All well...
            manholes.append(manhole)

        except Exception as e:
            _log2(node, expr, e, error_log)

    return manholes


def _drains(tree, mode, error_log):
    """Return a list of drains.

    """
    drains = []

    nodes = tree.xpath('//ZB_E', namespaces=NS)

    # In inspection mode, skip all drains without an inspection date.
    # EBF must be present for a drain considered to be inspected!

    for node in nodes:

        try:

            # EAA: drain reference

            expr = 'EAA'
            item = node.xpath(expr, namespaces=NS)[0]
            drain_ref = item.text.strip()
            drain = models.Drain(drain_ref)
            drain.sourceline = item.sourceline

            # EAB: drain coordinates
            # Occurrence: 0..1
            # gml:coordinates is deprecated in favour of gml:pos
            # The spec uses gml:point? gml:Point is correct!

            expr = 'EAB/gml:Point/gml:pos'
            node_set = node.xpath(expr, namespaces=NS)

            if node_set:
                coordinates = map(float, node_set[0].text.split())
                point = ogr.Geometry(ogr.wkbPoint)
                point.AddPoint(*coordinates)
                drain.geom = point

            # EAQ: Ownership
            node_set = node.xpath('EAQ')
            if node_set and node_set[0].text:
                drain.owner = node_set[0].text.strip()

            # EBF: inspection date
            # Occurrence: 0 for pre-inspection?
            # Occurrence: 1 for inspection?

            expr = 'EBF'
            node_set = node.xpath(expr, namespaces=NS)

            if mode == Mode.PREINSPECTION and len(node_set) != 0:
                msg = "maxOccurs = 0 in {}".format(mode)
                raise Exception(msg)

            if mode == Mode.INSPECTION and len(node_set) < 1:
                msg = "minOccurs = 1 in {}".format(mode)
                raise Exception(msg)

            if mode == Mode.INSPECTION and len(node_set) > 1:
                msg = "maxOccurs = 1 in {}".format(mode)
                raise Exception(msg)

            if mode == Mode.INSPECTION:
                drain.inspection_date = datetime.strptime(
                    node_set[0].text.strip(),
                    "%Y-%m-%d"
                )

            # ZC: observation
            # Occurrence: 0 for pre-inspection
            # Occurrence: * for inspection
            expr = 'ZC'
            node_set = node.xpath(expr, namespaces=NS)

            if mode == Mode.PREINSPECTION and len(node_set) != 0:
                msg = "maxOccurs = 0 in {}".format(mode)
                raise Exception(msg)

            for zc_node in node_set:
                observation = models.Observation(zc_node)
                drain.media.update(observation.media())

            # All well...
            drains.append(drain)

        except Exception as e:
            _log2(node, expr, e, error_log)

    return drains
