import os
import unittest

from ribxlib.parsers import Mode
from ribxlib.parsers import parse

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


class RibxTest(unittest.TestCase):

    def test_case_1(self):
        mode = Mode.INSPECTION
        f = os.path.join(DATA_DIR, "237_0-2013-D.ribx")
        parse(f, mode)

    def test_case_2(self):
        mode = Mode.INSPECTION
        f = os.path.join(DATA_DIR, "237_0-2013-R.ribx")
        parse(f, mode)

    def test_case_3(self):
        mode = Mode.INSPECTION
        f = os.path.join(DATA_DIR, "demobestand.ribxA")
        parse(f, mode)
