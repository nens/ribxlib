import os
import unittest

from ribxlib.parsers import RibxParser

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


class RibxTest(unittest.TestCase):

    def test_case_1(self):
        parser = RibxParser()
        f = os.path.join(DATA_DIR, "237_0-2013-D.ribx")
        parser.parse(f)

    def test_case_2(self):
        parser = RibxParser()
        f = os.path.join(DATA_DIR, "237_0-2013-R.ribx")
        parser.parse(f)

    def test_case_3(self):
        parser = RibxParser()
        f = os.path.join(DATA_DIR, "demobestand.ribxA")
        parser.parse(f)
