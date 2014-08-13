#!/usr/bin/env python
"""
_logger_

Basic logger for cirrus
"""
import sys
import logging


_LOGGER=None
_FORMATTER = logging.Formatter(
    "%(asctime)s;%(levelname)s;%(message)s",
    datefmt="%Y-%m-%d"
)


def get_logger():
    """
    set up a simple logger with stdout handler
    """
    global _LOGGER
    if _LOGGER is None:
        logger = logging.getLogger('cirrus_logger')
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setLevel(logging.INFO)
        handler.setFormatter(_FORMATTER)
        logger.addHandler(handler)
        _LOGGER = logger
    return _LOGGER
