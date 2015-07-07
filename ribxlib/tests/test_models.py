import unittest

from ribxlib import models


class ModelTest(unittest.TestCase):

    def test_case_1(self):
        """Docstring.

        """
        ribx = models.Ribx()

        pipe = models.CleaningPipe("Pipe")
        ribx.cleaning_pipes.append(pipe)

        manhole1 = models.CleaningManhole("Manhole1")
        pipe.manhole1 = manhole1

        manhole2 = models.CleaningManhole("Manhole2")
        pipe.manhole2 = manhole2

        manhole3 = models.CleaningManhole("Manhole3")
        ribx.cleaning_manholes.append(manhole3)

        drain = models.Drain("Drain")
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
