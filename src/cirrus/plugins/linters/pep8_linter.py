#!/usr/bin/env python
"""
pep8/pycodestyle linter

"""

import pycodestyle

from cirrus.linter_plugin import Linter
from cirrus.logger import get_logger

LOGGER = get_logger()


class Pep8(Linter):
    """
    Plugin to run pep8/pycodestyle on selected files

    """
    def __init__(self):
        super(Pep8, self).__init__()
        self.errors_per_file = int(self.linter_config.get(
            'allowed_errors_per_file', 0
        ))

    def run_linter(self, *files):
        """
        run pycodestyle checker on each file,
        check number of failures against a threshold
        """
        pep8_style = pycodestyle.StyleGuide(quiet=False)
        for file in files:
            LOGGER.info("Pep8: {}".format(file))
            errs = pep8_style.input_file(file)
            if errs:
                LOGGER.warning("Found {} errors".format(errs))
            if errs > self.errors_per_file:
                self.report_error(
                    file,
                    "{} pep8 errors in {}".format(errs, file)
                )
