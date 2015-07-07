import unittest

from lxml.etree import XML
from lxml.etree import fromstring

from ribxlib import models
from ribxlib import parsers


class TestInspectionPipeParser(unittest.TestCase):
    def setUp(self):
        self.parser = parsers.ElementParser(
            None, models.InspectionPipe, parsers.Mode.INSPECTION)

    def test_work_impossible(self):
        self.parser.node = fromstring("""
        <ZB_A xmlns:gml="http://www.opengis.net/gml">
          <AAA>whee</AAA>
          <AAD>16D0019</AAD>
          <AAE>
            <gml:Point srsDimension="2" srsName="Netherlands-RD">
              <gml:pos>144054.76 488764.43</gml:pos>
            </gml:Point>
          </AAE>
          <AAF>16D0021</AAF>
          <AAG>
            <gml:Point srsDimension="2" srsName="Netherlands-RD">
              <gml:pos>144003.23 488739.40</gml:pos>
            </gml:Point>
          </AAG>
          <ABF>2015-7-3</ABF>
          <ADE>Explanation in ADE</ADE>
          <AXD ADE="Explanation in attribute">Z</AXD>
        </ZB_A>
        """)
        instance = self.parser.parse()

        self.assertTrue(instance)
        self.assertTrue(instance.work_impossible)
        self.assertTrue('Andere reden' in instance.work_impossible)
        self.assertTrue(
            'Explanation in ADE' in instance.work_impossible)
        self.assertTrue(
            'Explanation in attribute' in instance.work_impossible)


class TestThingParser(unittest.TestCase):
    def setUp(self):
        self.parser = parsers.ElementParser(
            None, models.Drain, parsers.Mode.INSPECTION)

    def test_item_is_not_new(self):
        self.parser.node = XML("""
        <ZB_E>
          <EAA>whee</EAA>
          <EBF>2015-7-3</EBF>
          <ZC>
          </ZC>
        </ZB_E>
        """)

        instance = self.parser.parse()
        self.assertFalse(instance.new)

    def test_item_with_xc_is_new(self):
        self.parser.node = XML("""
        <ZB_E>
          <EAA>whee</EAA>
          <EBF>2015-7-3</EBF>
          <EXC>Don't know what kind of values go here</EXC>
          <ZC>
          </ZC>
        </ZB_E>
        """)

        instance = self.parser.parse()
        self.assertTrue(instance.new)
