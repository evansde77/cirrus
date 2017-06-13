#!/usr/bin/env python
"""
invoke_helpers

"""
import invoke
from .logger import get_logger


LOGGER = get_logger()


def local(command):
    """
    _local_

    fabric.operations local like command

    """
    c = invoke.Context()
    LOGGER.info("local({})".format(command))
    try:
        result = c.run(command)
    except invoke.exceptions.UnexpectedExit:
        msg = "Error running command:\n{}\n{}".format(result.stdout, result.stderr)
        LOGGER.error(msg)
        raise
