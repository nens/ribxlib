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

from ribxlib.models import Drain
from ribxlib.models import Manhole
from ribxlib.models import Pipe
from ribxlib.models import Ribx

logger = logging.getLogger(__name__)

NS = {
    "gml": "http://www.opengis.net/gml",
    "nl": "http://www.w3.org/2001/XMLSchema-instance",
}


class Mode(Enum):
    PREINSPECTION = 1
    INSPECTION = 2


def parse(f, mode):
    """Parse a GWSW.Ribx / GWSW.Ribx-A document.

    """
    parser = etree.XMLParser()

    try:
        tree = etree.parse(f, parser)
    except etree.XMLSyntaxError as e:
        logger.error(e)
        return Ribx(), _log(parser)

    # At this point, the document is well formed.

    # Even if no exception was raised, the error log might not be empty: it may
    # contain warnings, for example. TODO: should these be returned as well?

    error_log = _log(parser)

    ribx = Ribx()
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

    # In inspection mode, skip all pipes without an inspection date.
    # ABF must be present for a pipe considered to be inspected!

    if mode == Mode.INSPECTION:
        expr = '//ABF/parent::*|//nl:GBF/parent::*'
    else:
        expr = '//AAA/parent::*|//nl:GAA/parent::*'

    nodes = tree.xpath(expr, namespaces=NS)

    for node in nodes:

        try:

            # AAA: pipe reference
            # Occurrence: 1

            expr = 'AAA|nl:GAA'
            pipe_ref = node.xpath(expr, namespaces=NS)[0].text.strip()
            pipe = Pipe(pipe_ref)

            # AAD: manhole1 reference
            # Occurrence: 1

            expr = 'AAD|nl:GAD'
            manhole1_ref = node.xpath(expr, namespaces=NS)[0].text.strip()
            manhole1 = Manhole(manhole1_ref)
            pipe.manhole1 = manhole1

            # AAF: manhole2 reference
            # Occurrence: 1

            expr = 'AAF|nl:GAF'
            manhole2_ref = node.xpath(expr, namespaces=NS)[0].text.strip()
            manhole2 = Manhole(manhole2_ref)
            pipe.manhole2 = manhole2

            # AAE: manhole1 coordinates
            # Occurrence: 0..1
            # gml:coordinates is deprecated in favour of gml:pos
            # gml:Point is correct!

            expr = 'AAE/gml:point/gml:pos|nl:GAE/gml:point/gml:pos'
            node_set = node.xpath(expr, namespaces=NS)

            if node_set:
                coordinates = map(float, node_set[0].text.split())
                point = ogr.Geometry(ogr.wkbPoint)
                point.AddPoint(*coordinates)
                pipe.manhole1.geom = point

            # AAG: manhole2 coordinates
            # Occurrence: 0..1
            # gml:coordinates is deprecated in favour of gml:pos
            # gml:Point is correct!

            expr = 'AAG/gml:point/gml:pos|nl:GAG/gml:point/gml:pos'
            node_set = node.xpath(expr, namespaces=NS)

            if node_set:
                coordinates = map(float, node_set[0].text.split())
                point = ogr.Geometry(ogr.wkbPoint)
                point.AddPoint(*coordinates)
                pipe.manhole2.geom = point

            # ABF: inspection date
            # Occurrence: 0 for pre-inspection
            # Occurrence: 1 for inspection

            expr = 'ABF|nl:GBF'
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

            expr = 'ABS|nl:GBS'
            node_set = node.xpath(expr, namespaces=NS)

            if mode == Mode.PREINSPECTION and len(node_set) != 0:
                msg = "maxOccurs = 0 in {}".format(mode)
                raise Exception(msg)

            if mode == Mode.INSPECTION and len(node_set) > 1:
                msg = "maxOccurs = 1 in {}".format(mode)
                raise Exception(msg)

            if node_set:
                video = node_set[0].text.strip()
                pipe.media.append(video)

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

    if mode == Mode.INSPECTION:
        expr = '//CBF/parent::*|//JBF/parent::*'
    else:
        expr = '//CAA/parent::*|//JAA/parent::*'

    nodes = tree.xpath(expr, namespaces=NS)

    for node in nodes:

        try:

            # CAA: manhole reference

            expr = 'CAA|nl:JAA'
            manhole_ref = node.xpath(expr, namespaces=NS)[0].text.strip()
            manhole = Manhole(manhole_ref)

            # CAB: manhole coordinates
            # Occurrence: 0..1
            # gml:coordinates is deprecated in favour of gml:pos
            # gml:Point is correct!

            expr = 'CAB/gml:point/gml:pos|nl:JAB/gml:point/gml:pos'
            node_set = node.xpath(expr, namespaces=NS)

            if node_set:
                coordinates = map(float, node_set[0].text.split())
                point = ogr.Geometry(ogr.wkbPoint)
                point.AddPoint(*coordinates)
                manhole.geom = point

            # CBF: inspection date
            # Occurrence: 0 for pre-inspection
            # Occurrence: 1 for inspection

            expr = 'CBF|nl:JBF'
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

            expr = 'CBS|nl:JBS'
            node_set = node.xpath(expr, namespaces=NS)

            if mode == Mode.PREINSPECTION and len(node_set) != 0:
                msg = "maxOccurs = 0 in {}".format(mode)
                raise Exception(msg)

            if mode == Mode.INSPECTION and len(node_set) > 1:
                msg = "maxOccurs = 1 in {}".format(mode)
                raise Exception(msg)

            if node_set:
                video = node_set[0].text.strip()
                manhole.media.append(video)

            # All well...

            manholes.append(manhole)

        except Exception as e:
            _log2(node, expr, e, error_log)

    return manholes


def _drains(tree, mode, error_log):
    """Return a list of drains.

    """
    drains = []

    nodes = tree.xpath('//EAA/parent::*', namespaces=NS)

    # In inspection mode, skip all drains without an inspection date.
    # EBF must be present for a drain considered to be inspected!

    if mode == Mode.INSPECTION:
        expr = '//EBF/parent::*'
    else:
        expr = '//EAA/parent::*'

    for node in nodes:

        try:

            # EAA: drain reference

            expr = 'EAA'
            drain_ref = node.xpath(expr, namespaces=NS)[0].text.strip()
            drain = Drain(drain_ref)

            # EAB: drain coordinates
            # Occurrence: 0..1
            # gml:coordinates is deprecated in favour of gml:pos
            # gml:Point is correct!

            expr = 'EAB/gml:point/gml:pos'
            node_set = node.xpath(expr, namespaces=NS)

            if node_set:
                coordinates = map(float, node_set[0].text.split())
                point = ogr.Geometry(ogr.wkbPoint)
                point.AddPoint(*coordinates)
                drain.geom = point

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

            # All well...

            drains.append(drain)

        except Exception as e:
            _log2(node, expr, e, error_log)

    return drains
