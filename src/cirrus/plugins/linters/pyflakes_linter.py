#!/usr/bin/env python
"""
pyflakes linter plugin
"""
import sys
from pyflakes.api import checkPath
from pyflakes import reporter
from cirrus._2to3 import StringIO

from cirrus.linter_plugin import Linter
from cirrus.logger import get_logger

LOGGER = get_logger()


class Pyflakes(Linter):
    """
    Run pyflakes on selected files
    """
    def __init__(self):
        super(Pyflakes, self).__init__()
        self.errors_per_file = int(self.linter_config.get(
            'allowed_errors_per_file', 0
        ))

    def run_linter(self, *files):
        """
        for each file, run pyflakes and capture the output
        flag if files have too many errors relative to configured
        threshold

        """
        capture_stdout = StringIO()
        reporter.Reporter(capture_stdout, sys.stderr)
        for file in files:
            LOGGER.info("Pyflakes: {}".format(file))
            result = checkPath(file)
            if result:
                LOGGER.warning("Found {} flakes".format(result))
            if result > self.errors_per_file:
                self.report_error(file, capture_stdout.getvalue())
