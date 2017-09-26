# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import ntpath
import os
import sys

from osgeo import ogr

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) < 2:
        logger.critical("Pass in a ribx filename")
        sys.exit(1)

    filename = sys.argv[1]
    logger.info("Reading %s", filename)
