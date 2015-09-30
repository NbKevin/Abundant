#!/usr/env/bin python
# -*- encoding: utf-8 -*-

"""
Logging support for abundant.
"""

import logging
import os
import sys
import json

__author__ = 'Kevin'

with open('init_config.json', mode='r', encoding='utf-8') as raw_init_config:
    INIT_CONFIG = json.load(raw_init_config)

ABUNDANT_LOG_PATH = os.path.join(
    INIT_CONFIG['MasterConfigDirectory'], 'abundant.log'
)
ABUNDANT_LOG_FILE_HANDLER = logging.FileHandler(
    ABUNDANT_LOG_PATH, encoding='utf-8'
)

ABUNDANT_LOG_STD_OUT_HANDLER = logging.StreamHandler(sys.stdout)

LOG_FORMAT = logging.Formatter('%(asctime)s | %(name)8s | %(module)10s | %(levelname)8s | %(message)s')
LOG_FORMAT.datefmt = '%d %b %Y %H:%M:%S'

ABUNDANT_LOG_FILE_HANDLER.setFormatter(LOG_FORMAT)
ABUNDANT_LOG_STD_OUT_HANDLER.setFormatter(LOG_FORMAT)

ABUNDANT_LOGGER = logging.getLogger('ABUNDANT')
ABUNDANT_LOGGER.setLevel(
    {'Debug': logging.DEBUG,
     'Info': logging.INFO,
     'Warning': logging.WARNING,
     'Error': logging.ERROR}[INIT_CONFIG['LoggingLevel']]
)
ABUNDANT_LOGGER.addHandler(ABUNDANT_LOG_STD_OUT_HANDLER)
ABUNDANT_LOGGER.addHandler(ABUNDANT_LOG_FILE_HANDLER)

ABUNDANT_LOGGER.debug('- - - - - - - - - - - - - -')
ABUNDANT_LOGGER.debug('Logger is ready')
