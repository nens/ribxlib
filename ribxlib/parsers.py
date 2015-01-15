# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from datetime import datetime
import logging

from lxml import etree
from osgeo import ogr

from ribxlib.models import Drain
from ribxlib.models import Manhole
from ribxlib.models import Pipe
from ribxlib.models import Ribx

logger = logging.getLogger(__name__)

NAMESPACES = {
    "gml": "http://www.opengis.net/gml",
}


def parse(f):
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
    ribx.pipes = _pipes(tree, error_log)
    ribx.manholes = _manholes(tree, error_log)
    ribx.drains = _drains(tree, error_log)

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


def _log2(node, expr, error_log):
    """Append to a list of parser errors.

    """
    message = "Element {} has problems with {}".format(node.tag, expr)
    error_log.append({'line': node.sourceline, 'message': message})


def _pipes(tree, error_log):
    """Return a list of pipes.

    """
    pipes = []
    nodes = tree.xpath('//AAA/parent::*')
    for node in nodes:

        try:
            # AAA: pipe reference
            # Occurrence: 1

            expr = 'AAA'
            pipe_ref = node.xpath(expr)[0].text.strip()
            pipe = Pipe(pipe_ref)
            pipes.append(pipe)

            # AAD: node1 reference
            # Occurrence: 1

            expr = 'AAD'
            manhole1_ref = node.xpath(expr)[0].text.strip()
            manhole1 = Manhole(manhole1_ref)
            pipe.node1 = manhole1

            # AAF: node2 reference
            # Occurrence: 1

            expr = 'AAF'
            manhole2_ref = node.xpath(expr)[0].text.strip()
            manhole2 = Manhole(manhole2_ref)
            pipe.node2 = manhole2

            # AAE: node1 coordinates
            # Occurrence: 0..1
            # gml:coordinates is deprecated in favour of gml:pos
            # gml:Point is correct!

            expr = 'AAE/gml:point/gml:pos'
            node_set = node.xpath(expr, namespaces=NAMESPACES)

            if node_set:
                coordinates = map(float, node_set[0].text.split())
                point = ogr.Geometry(ogr.wkbPoint)
                point.AddPoint(*coordinates)
                pipe.node1.geom = point

            # AAG: node2 coordinates
            # Occurrence: 0..1
            # gml:coordinates is deprecated in favour of gml:pos
            # gml:Point is correct!

            expr = 'AAG/gml:point/gml:pos'
            node_set = node.xpath(expr, namespaces=NAMESPACES)

            if node_set:
                coordinates = map(float, node_set[0].text.split())
                point = ogr.Geometry(ogr.wkbPoint)
                point.AddPoint(*coordinates)
                pipe.node2.geom = point

            # ABF: inspection date
            # Occurrence: 1

            expr = 'ABF'
            inspection_date = datetime.strptime(
                node.xpath(expr)[0].text.strip(),
                "%Y-%m-%d"
            )

            # ABG: inspection time
            # Occurrence: 0..1

            expr = 'ABG'
            node_set = node.xpath(expr)

            if node_set:
                inspection_time = datetime.strptime(
                    node_set[0].text.strip(),
                    "%H:%M"
                ).time()

                inspection_date = datetime.combine(
                    inspection_date,
                    inspection_time
                )

            pipe.inspection_date = inspection_date

        except Exception as e:
            logger.error(e)
            _log2(node, expr, error_log)

    return pipes


def _manholes(tree, error_log):
    """Return a list of manholes.

    """
    manholes = []
    nodes = tree.xpath('//CAA/parent::*')
    for node in nodes:

        try:
            # CAA: manhole reference

            expr = 'CAA'
            manhole_ref = node.xpath(expr)[0].text.strip()
            manhole = Manhole(manhole_ref)
            manholes.append(manhole)

            # CAB: manhole coordinates
            # Occurrence: 0..1
            # gml:coordinates is deprecated in favour of gml:pos
            # gml:Point is correct!

            expr = 'CAB/gml:point/gml:pos'
            node_set = node.xpath(expr, namespaces=NAMESPACES)

            if node_set:
                coordinates = map(float, node_set[0].text.split())
                point = ogr.Geometry(ogr.wkbPoint)
                point.AddPoint(*coordinates)
                manhole.geom = point

            # CBF: inspection date
            # Occurrence: 1

            expr = 'CBF'
            inspection_date = datetime.strptime(
                node.xpath(expr)[0].text.strip(),
                "%Y-%m-%d"
            )

            # CBG: inspection time
            # Occurrence: 0..1

            expr = 'CBG'
            node_set = node.xpath(expr)

            if node_set:

                inspection_time = datetime.strptime(
                    node_set[0].text.strip(),
                    "%H:%M"
                ).time()

                inspection_date = datetime.combine(
                    inspection_date,
                    inspection_time
                )

            manhole.inspection_date = inspection_date

        except Exception as e:
            logger.error(e)
            _log2(node, expr, error_log)

    return manholes


def _drains(tree, error_log):
    """Return a list of drains.

    """
    drains = []
    nodes = tree.xpath('//EAA/parent::*')
    for node in nodes:

        try:
            # EAA: drain reference

            expr = 'EAA'
            drain_ref = node.xpath(expr)[0].text.strip()
            drain = Drain(drain_ref)
            drains.append(drain)

            # EAB: drain coordinates
            # Occurrence: 0..1
            # gml:coordinates is deprecated in favour of gml:pos
            # gml:Point is correct!

            expr = 'EAB/gml:point/gml:pos'
            node_set = node.xpath(expr, namespaces=NAMESPACES)

            if node_set:
                coordinates = map(float, node_set[0].text.split())
                point = ogr.Geometry(ogr.wkbPoint)
                point.AddPoint(*coordinates)
                drain.geom = point

            # EBF: inspection date
            # Occurrence: 1

            expr = 'EBF'
            inspection_date = datetime.strptime(
                node.xpath(expr)[0].text.strip(),
                "%Y-%m-%d"
            )

            # EBG: inspection time
            # Occurrence: 0..1

            expr = 'EBG'
            node_set = node.xpath(expr)

            if node_set:

                inspection_time = datetime.strptime(
                    node_set[0].text.strip(),
                    "%H:%M"
                ).time()

                inspection_date = datetime.combine(
                    inspection_date,
                    inspection_time
                )

            drain.inspection_date = inspection_date

        except Exception as e:
            logger.error(e)
            _log2(node, expr, error_log)

    return drains
