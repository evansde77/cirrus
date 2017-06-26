#!/usr/bin/env python
"""
invoke_helpers

"""
from invoke import Context
from invoke.exceptions import UnexpectedExit
from .logger import get_logger


LOGGER = get_logger()


def local(command):
    """
    _local_

    fabric.operations local like command

    """
    c = Context()
    LOGGER.info("local({})".format(command))
    try:
        result = c.run(command)
    except UnexpectedExit as ex:
        msg = "Error running command:\n{}".format(ex)
        LOGGER.error(msg)
        raise
