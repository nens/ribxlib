import os
import unittest

from ribxlib.parsers import _check_filename
from ribxlib.parsers import Mode
from ribxlib.parsers import parse

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


class RibxTest(unittest.TestCase):

    def test_case_1(self):
        mode = Mode.INSPECTION
        f = os.path.join(DATA_DIR, "237_0-2013-D.ribx")
        ribx, log = parse(f, mode)
        ##self.assertFalse(log)
        self.assertFalse(len(log))

    def test_case_2(self):
        mode = Mode.INSPECTION
        f = os.path.join(DATA_DIR, "237_0-2013-R.ribx")
        ribx, log = parse(f, mode)
        ##self.assertFalse(log)
        self.assertFalse(len(log))

    def test_case_3(self):
        mode = Mode.INSPECTION
        f = os.path.join(DATA_DIR, "demobestand.ribxA")
        ribx, log = parse(f, mode)
        ##self.assertFalse(log)
        self.assertFalse(len(log))

    def test_case_4(self):
        self.assertRaises(
            Exception,
            _check_filename,
            "C:\user\docs\Letter.txt"
        )

    def test_case_5(self):
        self.assertRaises(
            Exception,
            _check_filename,
            "\\Server01\user\docs\Letter.txt"
        )

    def test_case_6(self):
        self.assertRaises(
            Exception,
            _check_filename,
            "/home/user/docs/Letter.txt"
        )

    def test_case_7(self):
        self.assertRaises(
            Exception,
            _check_filename,
            "Letter"
        )

    def test_case_8(self):
        self.assertRaises(
            Exception,
            _check_filename,
            ".txt"
        )
