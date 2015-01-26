import unittest

from ribxlib.models import Drain
from ribxlib.models import Manhole
from ribxlib.models import Pipe
from ribxlib.models import Ribx


class ModelTest(unittest.TestCase):

    def test_case_1(self):
        """Docstring.

        """
        ribx = Ribx()

        pipe = Pipe("Pipe")
        ribx.pipes.append(pipe)

        manhole1 = Manhole("Manhole1")
        pipe.manhole1 = manhole1

        manhole2 = Manhole("Manhole2")
        pipe.manhole2 = manhole2

        manhole3 = Manhole("Manhole3")
        ribx.manholes.append(manhole3)

        drain = Drain("Drain")
        ribx.drains.append(drain)

        pipe.media.add("video.mpg")
        manhole1.media.add("manhole1.png")
        manhole2.media.add("manhole2.png")
        manhole3.media.add("manhole3.png")
        drain.media.add("drain.jpg")
        drain.media.add("drain.png")

        expected = set([
            'video.mpg',
            'manhole1.png',
            'manhole2.png',
            'manhole3.png',
            'drain.jpg',
            'drain.png',
        ])

        self.assertEqual(expected, ribx.media)
