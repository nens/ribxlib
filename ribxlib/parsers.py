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

    inspection_pipe_parser = TreeParser(
        tree, models.InspectionPipe, mode, error_log)
    cleaning_pipe_parser = TreeParser(
        tree, models.CleaningPipe, mode, error_log)
    drain_parser = TreeParser(
        tree, models.Drain, mode, error_log)
    inspection_manhole_parser = TreeParser(
        tree, models.InspectionManhole, mode, error_log)
    cleaning_manhole_parser = TreeParser(
        tree, models.CleaningManhole, mode, error_log)

    ribx.inspection_pipes = inspection_pipe_parser.elements()
    ribx.cleaning_pipes = cleaning_pipe_parser.elements()
    ribx.inspection_manholes = inspection_manhole_parser.elements()
    ribx.cleaning_manholes = cleaning_manhole_parser.elements()
    ribx.drains = drain_parser.elements()

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


class TreeParser(object):
    """Parser for any kind of thing (Pipe / Manhole / Drain); all the tags
    work very similarly, except for different prefixes.

    """

    def __init__(self, tree, model, mode, error_log):
        self.tree = tree
        self.model = model
        self.mode = mode
        self.error_log = error_log

    def elements(self):
        """Return all SewerElement model instances that are in the tree."""
        elements = []

        nodes = self.tree.xpath('//{}'.format(self.model.tag), namespaces=NS)

        for node in nodes:
            element_parser = ElementParser(node, self.model, self.mode)
            try:
                instance = element_parser.parse()
                if instance:
                    elements.append(instance)
            except Exception as e:
                _log2(node, element_parser.expr, e, self.error_log)

        return elements


class ElementParser(object):
    """Parse an individual node."""
    def __init__(self, node, model, mode):
        self.node = node
        self.model = model
        self.mode = mode

        self.expr = ''  # Keep it around so we can log it in case of error

    def xpath(self, expr):
        self.expr = expr
        return self.node.xpath(expr, namespaces=NS)

    def tag(self, name):
        return self.model.tag[-1] + name

    def parse(self):
        # ?AA: reference
        item_ref, item_sourceline = self.tag_value('AA', complain=True)
        instance = self.model(item_ref)
        instance.sourceline = item_sourceline

        instance.inspection_date = self.get_inspection_date()
        instance.inspection_datetime = self.get_inspection_date_with_time()

        if issubclass(self.model, models.Pipe):
            # We need two manholes and two sets of coordinates.
            manhole1_ref, manhole1_sourceline = self.tag_value(
                'AD', complain=True)
            instance.manhole1 = models.Manhole(manhole1_ref)
            instance.manhole1.sourceline = manhole1_sourceline
            instance.manhole1.geom = self.tag_point('AE')

            manhole2_ref, manhole2_sourceline = self.tag_value(
                'AF', complain=True)
            instance.manhole2 = models.Manhole(manhole2_ref)
            instance.manhole2.sourceline = manhole2_sourceline
            instance.manhole2.geom = self.tag_point('AG')

            if issubclass(self.model, models.InspectionPipe):
                if self.mode == Mode.INSPECTION:
                    instance.manhole_start = self.get_manhole_start(instance)

        else:
            # ?AB holds coordinates
            instance.geom = self.tag_point('AB')

        # ?AQ: Ownership
        instance.owner = self.tag_value('AQ')[0]

        if self.model.has_video:
            instance.media.update(self.get_video())

        # Maybe inspection / cleaning wasn't possible
        instance.work_impossible = self.get_work_impossible()

        # If a *XC tag exists, this element was new, not planned
        # *XC = "Ontbreekt in opracht"
        if self.xpath(self.tag('XC')):
            instance.new = True

        # ZC nodes
        for observation in self.get_observations():
            instance.media.update(observation.media())

        # All well...
        return instance

    def tag_value(self, name, complain=False):
        items = self.xpath(self.tag(name))
        if not items:
            if complain:
                raise models.ParseException(
                    "Expected {} record".format(self.tag(name)))
            else:
                return None, None
        item = items[0]
        return item.text.strip(), item.sourceline

    def tag_attribute(self, name, attribute):
        item = self.xpath('{}/@{}'.format(self.tag(name), self.tag(attribute)))
        if item:
            return item[0]

    def tag_point(self, name):
        """Interpret tag contents as gml:Point and return geom"""
        node_set = self.xpath('{}/gml:Point/gml:pos'.format(self.tag(name)))

        if node_set:
            coordinates = map(float, node_set[0].text.split())
            point = ogr.Geometry(ogr.wkbPoint)
            point.AddPoint(*coordinates)
            return point

    def get_manhole_start(self, instance):
        """Return a manhole ref that references the starting manhole of
        a Pipe inspection, which corresponds to either manhole1 or manhole2 of
        the pipe."""
        manhole_start_ref, manhole_start_sourceline = self.tag_value('AB')
        if (manhole_start_ref and manhole_start_ref not in
                [instance.manhole1.ref, instance.manhole2.ref]):
            raise Exception(
                "manhole_start {} doesn't correspond to either manhole1 {} or "
                "manhole2 {} of the pipe.".format(manhole_start_ref,
                                                  instance.manhole1.ref,
                                                  instance.manhole2.ref))

        if not manhole_start_ref:
            raise Exception("Inspection start node for pipes must be present. "
                            "Current mode: {}".format(self.mode))
        return manhole_start_ref

    def get_work_impossible(self):
        xd, sourceline = self.tag_value('XD')
        if xd:
            xd_explanation = {
                'A': 'Voertuig/obstakel op toegang',
                'B': 'Straat niet toegankelijk voor het voertuig',
                'C': 'Groen blokkeert de toegang',
                'D': 'Niet aangetroffen',
                'E': 'Deksel vast',
                'Z': 'Andere reden.'
            }.get(xd, None)

            if xd_explanation is None:
                raise Exception('Onbekende {}XD code "{}"'.format(
                    self.tag('XD'), xd))

            attr_explanation = self.tag_attribute('XD', 'DE') or ''
            if xd == 'Z' and not attr_explanation:
                raise Exception(
                    'Expected explanation for Z code in {} tag'
                    .format(self.tag('DE')))
            elif xd != 'Z' and attr_explanation:
                raise Exception(
                    'Explanation in {} tag not allowed without Z code.'
                    .format(self.tag('DE')))

            tag_explanation, sourceline = self.tag_value('DE')

            explanation = "{} ({})\n{}\n{}".format(
                xd_explanation, xd, attr_explanation,
                tag_explanation).strip()

            return explanation

    def get_inspection_date(self, as_string=False):
        """?BF: inspection date
        In inspection mode, skip everything without an inspection date.
        ?BF must be present for something considered to be inspected!
        Occurrence: 0 for pre-inspection
        Occurrence: 1 for inspection

        Args:
            as_string: if True, return as string, else convert to datetime
        """
        node_set = self.xpath(self.tag('BF'))

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
            if as_string:
                return node_set[0].text.strip()
            else:
                return datetime.strptime(
                    node_set[0].text.strip(),
                    "%Y-%m-%d"
                )
        else:
            return None

    def get_inspection_date_with_time(self):
        """?BG: inspection date including the time.

        ?BG is always an optional field, while the date (?BF) is required in
        INSPECTION mode. This method will combine both ?BF and ?BG into one
        single datetime when a ?BG tag is found (there is a bit of
        redundancy here).

        Occurrence: 0 for pre-inspection
        Occurrence: 0..1 for inspection
        """
        node_set = self.xpath(self.tag('BG'))

        if self.mode == Mode.PREINSPECTION and len(node_set) != 0:
            msg = "maxOccurs = 0 in {}".format(self.mode)
            raise Exception(msg)
        if self.mode == Mode.INSPECTION and len(node_set) > 0:
            date = self.get_inspection_date(as_string=True)
            time = node_set[0].text.strip()
            return datetime.strptime(
                '{} {}'.format(date, time),
                "%Y-%m-%d %H:%M:%S"
            )
        return None

    def get_video(self):
        # ?BS: file name of video
        # Occurrence: 0 for pre-inspection
        # Occurrence: 0..1 for inspection
        node_set = self.xpath(self.tag('BS'))

        if self.mode == Mode.PREINSPECTION and len(node_set) != 0:
            msg = "maxOccurs = 0 in {}".format(self.mode)
            raise Exception(msg)

        if self.mode == Mode.INSPECTION and len(node_set) > 1:
            msg = "maxOccurs = 1 in {}".format(self.mode)
            raise Exception(msg)

        if node_set:
            video = node_set[0].text.strip()
            models._check_filename(video)
            return set([video])
        else:
            return set([])

    def get_observations(self):
        # ZC: observation
        # Occurrence: 0 for pre-inspection
        # Occurrence: * for inspection
        node_set = self.xpath('ZC')

        if self.mode == Mode.PREINSPECTION and len(node_set) != 0:
            msg = "maxOccurs = 0 in {}".format(self.mode)
            raise Exception(msg)

        for zc_node in node_set:
            yield models.Observation(zc_node)
