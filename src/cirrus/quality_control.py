'''
_quality_control_

Command to run quality control via pylint, pep8, pyflakes
'''
import sys
from argparse import ArgumentParser

from git_tools import get_diff_files
from pylint_tools import pep8_file
from pylint_tools import pyflakes_file
from pylint_tools import pylint_file
from cirrus.configuration import load_configuration
from cirrus.logger import get_logger

LOGGER = get_logger()


def build_parser(argslist):
    """
    _build_parser_

    Set up command line parser for the qc command

    """
    parser = ArgumentParser(
        description=('git cirrus qc command: runs pep8, pylint, and pyflakes'
            'on source code and generates an acceptance code')
    )
    parser.add_argument('qc', nargs='?')
    parser.add_argument(
        '-f',
        '--files',
        dest='files',
        nargs='+',
        required=False,
        help='specify files to run qc on')
    parser.add_argument('--pylint', action='store_true')
    parser.add_argument('--pyflakes', action='store_true')
    parser.add_argument('--pep8', action='store_true')
    parser.add_argument(
        '--only-changes',
        action='store_true',
        help='Only run quality control on packages that you are working on')
    parser.add_argument('-v', '--verbose', action='store_true')

    opts = parser.parse_args(argslist)

    if opts.only_changes and opts.files is not None:
        raise("Cannot set '--only-changes=True' and provide an list of files")

    return opts


def run_pylint(files=None):
    """
    Runs pylint on a package or list of files
    """
    config = load_configuration()
    quality_info = ()
    pylint_options = {'rcfile': config.quality_rcfile()}
    if files == None:  # run on entire package
        quality_info = pylint_file(
            [config.package_name()],
            **pylint_options)
    else:
        quality_info = pylint_file(
            files,
            **pylint_options)

    threshold = config.quality_threshold()
    if quality_info[1] <= threshold:
        LOGGER.info(("Failed threshold test.  "
            "Your score: {0}, Threshold {1}".format(
                quality_info[1], threshold)))
    else:
        LOGGER.info("Passed threshold test.")


def run_pyflakes(verbose, files=None):
    """
    Runs pyflakes on a package or list of files
    """
    config = load_configuration()
    quality_info = ()
    if files == None:  # run on entire package
        quality_info = pyflakes_file([config.package_name()], verbose=verbose)
    else:
        quality_info = pyflakes_file(files, verbose=verbose)

    LOGGER.info("Package ran: {0}, Number of Flakes: {1}".format(
        quality_info[0],
        quality_info[1]))


def run_pep8(verbose, files=None):
    """
    Runs pep8 on a package or list of files
    """
    config = load_configuration()
    quality_info = ()
    if files == None:  # run on entire package
        quality_info = pep8_file([config.package_name()], verbose=verbose)
    else:
        quality_info = pep8_file(files, verbose=verbose)

    LOGGER.info("Package ran: {0}, Number of Errors: {1}".format(
        quality_info[0],
        quality_info[1]))


def main():
    """
    _main_

    Execute test command
    """
    opts = build_parser(sys.argv)
    if opts.only_changes:
        files = get_diff_files(None)
        #we only want python modules
        for item in files:
            if not item.endswith('.py'):
                files.remove(item)
        if not files:
            LOGGER.info("No modules have been changed.")
            exit(0)
    else:
        files = opts.files
    #run all if none specified
    if not opts.pylint and not opts.pep8 and not opts.pyflakes:
        run_pep8(opts.verbose, files=files)
        run_pyflakes(opts.verbose, files=files)
        run_pylint(files=files)
    else:
        if opts.pylint:
            run_pylint(files=files)
        if opts.pep8:
            run_pep8(opts.verbose, files=files)
        if opts.pyflakes:
            run_pyflakes(opts.verbose, files=files)

if __name__ == '__main__':
    main()
