import os
import unittest

from lxml.etree import XML
from lxml.etree import fromstring

from ribxlib import models
from ribxlib import parsers
from ribxlib.parsers import Mode
from ribxlib.parsers import parse

RIBX13_DATA_DIR = os.path.join(
    os.path.dirname(__file__), '..', '..', 'testdata', 'ribx_13')


class TestInspectionPipeParser(unittest.TestCase):
    def setUp(self):
        self.parser = parsers.ElementParser(
            None, models.InspectionPipe, parsers.Mode.INSPECTION)

    def test_work_impossible(self):
        self.parser.node = fromstring("""
        <ZB_A xmlns:gml="http://www.opengis.net/gml">
          <AAA>whee</AAA>
          <AAB>16D0019</AAB>
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
          <ABQ>25</ABQ>
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


class TestInspectionPipeParserRibx_13(unittest.TestCase):
    """Test regarding version 1.3 of Ribx."""

    def test_ribx_13_smoke(self):
        mode = Mode.INSPECTION
        f = os.path.join(RIBX13_DATA_DIR, "36190148 5300093.ribx")
        ribx, log = parse(f, mode)
        # self.assertFalse(log)
        self.assertFalse(len(log))

    def test_ribx_13_manhole_start_set(self):
        """This ribx has two inspection headers with the same Pipe ref. For
        inspection of Pipes the manhole_start attribute must be set.
        """
        mode = Mode.INSPECTION
        f = os.path.join(RIBX13_DATA_DIR, "36190148 5300093.ribx")
        ribx, log = parse(f, mode)

        p0, p1 = ribx.inspection_pipes  # there are only 2 pipes (see file)

        self.assertEqual(p0.ref, p1.ref)
        self.assertNotEqual(p0.manhole_start, p1.manhole_start)

    def test_ribx_13_manhole_start_consistent(self):
        """Test that manhole_start is one of the two manholes of the pipe."""
        mode = Mode.INSPECTION
        f = os.path.join(RIBX13_DATA_DIR, "36190148 5300093.ribx")
        ribx, log = parse(f, mode)
        p0, p1 = ribx.inspection_pipes

        self.assertTrue(
            p0.manhole_start in [p0.manhole1.ref, p0.manhole2.ref])
        self.assertTrue(
            p1.manhole_start in [p1.manhole1.ref, p1.manhole2.ref])


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

    def test_item_without_time(self):
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
        self.assertEqual(str(instance.inspection_date), '2015-07-03 00:00:00')

    def test_item_with_bg_has_time(self):
        self.parser.node = XML("""
        <ZB_E>
          <EAA>whee</EAA>
          <EBF>2015-7-3</EBF>
          <EBG>14:02:56</EBG>
          <EXC>Don't know what kind of values go here</EXC>
          <ZC>
          </ZC>
        </ZB_E>
        """)

        instance = self.parser.parse()
        self.assertTrue(instance.inspection_date)
        self.assertEqual(str(instance.inspection_date),
                         '2015-07-03 14:02:56')

    def test_item_with_only_time(self):
        """This case should never occur, a date *must* be supplied."""
        self.parser.node = XML("""
        <ZB_E>
          <EAA>whee</EAA>
          <EBG>14:02:56</EBG>
          <EXC>Don't know what kind of values go here</EXC>
          <ZC>
          </ZC>
        </ZB_E>
        """)

        with self.assertRaises(Exception):
            self.parser.parse()
