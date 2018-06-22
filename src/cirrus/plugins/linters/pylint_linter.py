#!/usr/bin/env python
"""
pylint linter
"""
import re

from cirrus.linter_plugin import Linter
from cirrus._2to3 import redirect_stdout, StringIO
from cirrus.logger import get_logger
from pylint.lint import Run


LOGGER = get_logger()

SCORE_MATCH = re.compile("[\-]*\d.\d\d")
ERROR_MATCH = re.compile("")


class Pylint(Linter):
    """
    Run pylint on matching files and flag any errors or files that
    dont meet configured QC standard

    """
    def __init__(self):
        super(Pylint, self).__init__()
        self.default_score = self.linter_config.get('default_score', 0)
        self.min_score = int(
            self.linter_config.get('minimum_score_per_file', 7)
        )
        self.rcfile = self.linter_config.get('pylintrc', None)

    def run_linter(self, *files):
        """
        process the list of files to be linted

        """
        for file in files:
            LOGGER.info("Pylinting {}".format(file))
            score, errors = self.lint_file(file)
            LOGGER.info("Score: {} {}".format(score, file))
            if errors:
                self.report_error(
                    file, "File {} has pylint errors".format(file)
                )
            if score < self.min_score:
                self.report_error(
                    file,
                    "File {} scored less than {}".format(file, self.min_score)
                )

    def lint_file(self, f):
        """
        run pyling on a file and get its pylint score,
        returns scrore and error count
        """
        outp = StringIO()
        with redirect_stdout(outp):
            # TODO add support for rcfile
            args = [f, "-r", "n"]
            if self.rcfile:
                args.append("--rcfile={}".format(self.rcfile))
            Run(args, exit=False)
        report = outp.getvalue()
        errors = 0
        score = self.default_score
        for line in report.split('\n'):
            if re.match("E....:.", line):
                LOGGER.warning("  => {}".format(line))
                errors += 1
            if "Your code has been rated at" in line:
                scores = SCORE_MATCH.findall(line)
                if not scores:
                    msg = "Could not find Pylint score for: {}".format(f)
                    LOGGER.warning(msg)
                    score = self.default_score
                else:
                    score = float(scores[0])
        return score, errors
