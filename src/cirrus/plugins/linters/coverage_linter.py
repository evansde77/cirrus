#!/usr/bin/env python
"""
coverage linter plugin
"""
import coverage

from cirrus.linter_plugin import Linter
from cirrus.logger import get_logger

LOGGER = get_logger()


class Coverage(Linter):

    def __init__(self):
        super(Coverage, self).__init__()
        self.errors_per_file = int(self.linter_config.get(
            'allowed_errors_per_file', 0
        ))

    def run_linter(self, *files):
        cov = coverage.Coverage()
        cov.start()
        for file in files:
            LOGGER.info("Coverage: {}".format(file))
            _, exec_stmt, missing, fmt = cov.analysis(file)
            num_missing = len(missing)
            if num_missing:
                LOGGER.warning("Missing {} coverage lines".format(num_missing))
            if num_missing > self.errors_per_file:
                self.report_error(
                    file, "Missing coverage lines: {}".format(fmt)
                )
        cov.stop()
