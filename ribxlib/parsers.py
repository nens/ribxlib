# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from lxml import etree
from osgeo import ogr

logger = logging.getLogger(__name__)

NAMESPACES = {
    "gml": "http://www.opengis.net/gml",
}


class Pipe(object):
    """Sewerage pipe (`rioolbuis` in Dutch).

    """
    def __init__(self, ref):
        self.ref = ref
        self.node1 = None  # Is a manhole?
        self.node2 = None  # Is a manhole?

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

    def __str__(self):
        return self.ref


class Drain(object):
    """A storm drain (`kolk` in Dutch).

    """
    def __init__(self, ref):
        self.ref = ref
        self.geom = None

    def __str__(self):
        return self.ref


class RibxParser(object):

    def parse(self, f):
        self.__tree = etree.parse(f)

    def pipes(self):
        """Return a list of pipes.

        """
        pipes = []
        nodes = self.__tree.xpath('//AAA/parent::*')
        for node in nodes:

            # AAA: pipe reference

            pipe_ref = node.xpath('AAA')[0].text.strip()
            pipe = Pipe(pipe_ref)
            pipes.append(pipe)

            # AAD: node1 reference
            # Occurrence: 1

            manhole1_ref = node.xpath('AAD')[0].text.strip()
            manhole1 = Manhole(manhole1_ref)
            pipe.node1 = manhole1

            # AAF: node2 reference
            # Occurrence: 1

            manhole2_ref = node.xpath('AAF')[0].text.strip()
            manhole2 = Manhole(manhole2_ref)
            pipe.node2 = manhole2

            # AAE: node1 coordinates
            # Occurrence: 0..1

            pos1 = node.xpath(
                'AAE/gml:point/gml:pos',  # gml:Point is correct!
                namespaces=NAMESPACES
            )

            if pos1:
                coordinates = map(float, pos1[0].text.split())
                point = ogr.Geometry(ogr.wkbPoint)
                point.AddPoint(*coordinates)
                pipe.node1.geom = point

            # AAG: node2 coordinates
            # Occurrence: 0..1

            pos2 = node.xpath(
                'AAG/gml:point/gml:pos',  # gml:Point is correct!
                namespaces=NAMESPACES
            )

            if pos2:
                coordinates = map(float, pos2[0].text.split())
                point = ogr.Geometry(ogr.wkbPoint)
                point.AddPoint(*coordinates)
                pipe.node2.geom = point

        return pipes

    def manholes(self):
        """Return a list of manholes.

        """
        manholes = []
        nodes = self.__tree.xpath('//CAA/parent::*')
        for node in nodes:

            # CAA: manhole reference

            manhole_ref = node.xpath('CAA')[0].text.strip()
            manhole = Manhole(manhole_ref)
            manholes.append(manhole)

            # CAB: manhole coordinates
            # Occurrence: 0..1

            pos = node.xpath(
                'CAB/gml:point/gml:pos',  # gml:Point is correct!
                namespaces=NAMESPACES
            )

            if pos:
                coordinates = map(float, pos[0].text.split())
                point = ogr.Geometry(ogr.wkbPoint)
                point.AddPoint(*coordinates)
                manhole.geom = point

        return manholes

    def drains(self):
        """Return a list of drains.

        """
        drains = []
        nodes = self.__tree.xpath('//EAA/parent::*')
        for node in nodes:

            # EAA: drain reference

            drain_ref = node.xpath('EAA')[0].text.strip()
            drain = Drain(drain_ref)
            drains.append(drain)

            # EAB: drain coordinates
            # Occurrence: 0..1

            pos = node.xpath(
                'EAB/gml:point/gml:pos',  # gml:Point is correct!
                namespaces=NAMESPACES
            )

            if pos:
                coordinates = map(float, pos[0].text.split())
                point = ogr.Geometry(ogr.wkbPoint)
                point.AddPoint(*coordinates)
                drain.geom = point

        return drains
