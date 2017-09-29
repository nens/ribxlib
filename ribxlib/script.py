# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import sys

from ribxlib import parsers

logger = logging.getLogger(__name__)

POSSIBLE_ITEM_LISTS = ['inspection_pipes',
                       'cleaning_pipes',
                       'inspection_manholes',
                       'cleaning_manholes',
                       'drains',
                   ]


def main():
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) < 2:
        logger.critical("Pass in a ribx filename")
        sys.exit(1)

    filename = sys.argv[1]
    logger.info("Reading %s (in 'inspection' mode)", filename)

    ribx, error_log = parsers.parse(open(filename), parsers.Mode.INSPECTION)
    if error_log:
        logger.error("Error log found:\n%s", error_log)

    for item_list_name in POSSIBLE_ITEM_LISTS:
        item_list = getattr(ribx, item_list_name)
        title = "%s: %s items" % (item_list_name, len(item_list))
        print(title)
        print('=' * len(title))
        print('')

        for item in item_list:
            item.print_for_debug()
            print('')
