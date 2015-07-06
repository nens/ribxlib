import unittest

from lxml.etree import XML

from ribxlib import models
from ribxlib import parsers


class TestThingParser(unittest.TestCase):
    def setUp(self):
        self.parser = parsers.ThingParser(
            None, models.Drain, parsers.Mode.INSPECTION)

    def test_work_impossible(self):
        self.parser.node = XML("""
        <ZB_E>
          <EAA>whee</EAA>
          <EBF>2015-7-3</EBF>
          <EDE>Explanation in EDE</EDE>
          <EXD EDE="Explanation in attribute">misc</EXD>
        </ZB_E>
        """)
        instance = self.parser.parse()

        self.assertTrue(instance)
        self.assertTrue(instance.work_impossible)

        self.assertTrue('misc' in instance.work_impossible)
        self.assertTrue(
            'Explanation in EDE' in instance.work_impossible)
        self.assertTrue(
            'Explanation in attribute' in instance.work_impossible)
