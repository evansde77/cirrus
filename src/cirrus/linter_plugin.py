#!/usr/bin/env python
"""
linter plugins for qc command

"""
import os
import fnmatch

from cirrus.configuration import load_configuration
from cirrus.environment import repo_directory

from pluggage.factory_plugin import PluggagePlugin
from cirrus.logger import get_logger


LOGGER = get_logger()


match_path = lambda x, xp: any(fnmatch.fnmatch(x, y) for y in xp)


def normalise_dir_pattern(repo_dir, d):
    """
    if d is a relative path, prepend the repo_dir to it
    """
    if not d.startswith(repo_dir):
        return os.path.join(repo_dir, d)
    else:
        return d


def python_files(
        repo_dir,
        exclude_dirs=None,
        exclude_files=None,
        include_files=None
        ):
    """
    iterate over all the python files found recursively in repo_dir

    Optionally exclude directory paths or file paths using fnmatch to allow
    glob style wildcards.

    Optionally explicitly whitelist files matching a glob pattern

    :param repo_dir: Location of repo to search
    :param exclude_dirs: List of glob patterns to exclude dirs
    :param exclude_files: List of glob patterns to exclude filenames
    :param include_files: List of glob patterns to include only these files

    """
    if exclude_dirs is None:
        exclude_dirs = []
    if exclude_files is None:
        exclude_files = []

    whitelist = None
    if include_files is not None:
        whitelist = []
        whitelist.extend(
            normalise_dir_pattern(repo_dir, x) for x in include_files
        )

    x_dirs = [normalise_dir_pattern(repo_dir, x) for x in exclude_dirs]
    x_files = [normalise_dir_pattern(repo_dir, x) for x in exclude_files]

    for d, subd, files in os.walk(repo_dir):
        if match_path(d, x_dirs):
            continue
        for file in files:
            file_path = os.path.join(d, file)
            if match_path(file_path, x_files):
                continue
            if not file.endswith('.py'):
                continue
            if whitelist:
                if not match_path(file_path, whitelist):
                    continue

            yield file_path


class Linter(PluggagePlugin):
    PLUGGAGE_FACTORY_NAME = 'linter'

    def __init__(self):
        super(Linter, self).__init__()
        self.config = load_configuration()
        self.linter_config = self.config.get(
            'qc/{}'.format(type(self).__name__, {}),
            {}
            )
        self.working_dir = repo_directory()
        self.pass_threshold = 0
        self.test_mode = False
        self.errors = {}

    def report_error(self, filename, message):
        reports = self.errors.setdefault(filename, [])
        reports.append(message)

    def find_files(self, opts):
        """
        return a list of files, optionally excluding or
        including directories or taking a list of cli options
        """
        files = [
            x for x in python_files(
                self.working_dir,
                exclude_dirs=opts.exclude_dirs,
                exclude_files=opts.exclude_files,
                include_files=opts.include_files
            )
        ]
        if not files:
            msg = (
                "Unable to match any files in dir {dir}\n"
                "excluding dirs: {x_dirs}\n"
                "excluding files: {x_files}\n"
                "including files: {i_files}\n"
            ).format(
                dir=self.working_dir,
                x_dirs=opts.exclude_dirs,
                x_files=opts.exclude_files,
                i_files=opts.include_files
            )
            LOGGER.error(msg)
            raise RuntimeError(msg)
        return files

    def run_linter(self, *files):
        """
        override linter, return a score
        """

    def check(self, opts):
        files = self.find_files(opts)
        if self.test_mode:
            for file in files:
                LOGGER.info(
                    "TEST MODE: {} {}".format(type(self).__name__, file)
                )
            result = 0
        else:
            result = self.run_linter(*files)
        return result
