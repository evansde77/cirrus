'''
_quality_control_

Command to run quality control via pylint, pep8, pyflakes
'''
import sys
from argparse import ArgumentParser

from pylint_tools import pep8_file
from pylint_tools import pyflakes
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
        description='git cirrus qc command'
    )
    parser.add_argument('qc', nargs='?')
    parser.add_argument(
        '-f',
        '--file',
        dest='file',
        required='false',
        help='specify file to run qc on')
    parser.add_argument('--pylint', action='store_true')
    parser.add_argument('--pyflakes', action='store_true')
    parser.add_argument('--pep8', action='store_true')
    parser.add_argument(
        '--changes',
        action='store_false',
        help='Only run quality control on packages that you are working on')

    opts = parser.parse_args(argslist)
    return opts


def run_pylint(file=None):
    config = load_configuration()
    quality_info = ()
    if file == None:  # run on entire package
        quality_info = pylint_file(
            config.package_name(),
            config.quality_rcfile())
    else:
        quality_info = pylint_file(file, config.quality_rcfile())

    threshold = config.quality_threshold()
    if quality_info[1] <= threshold:
        LOGGER.info(("Failed threshold test.  "),
            ("Your score: {0}, Threshold {1}".format(
                quality_info[1], threshold)))
    else:
        LOGGER.info("Passed threshold test.")


def run_pyflakes(file=None):
    config = load_configuration()
    quality_info = ()
    if file == None:  # run on entire package
        quality_info = pyflakes(config.package_name())
    else:
        quality_info = pyflakes(file)

    LOGGER.info("Package ran: {0}, Number of Flakes: {1}".format(
        quality_info[0],
        quality_info[1]))


def run_pep8(file=None):
    config = load_configuration()
    quality_info = ()
    if file == None:  # run on entire package
        quality_info = pep8_file(config.package_name())
    else:
        quality_info = pep8_file(file)

    LOGGER.info("Package ran: {0}, Number of Errors: {1}".format(
        quality_info[0],
        quality_info[1]))


def main():
    """
    _main_

    Execute test command
    """
    opts = build_parser(sys.argv)
    #run all if none specified
    if not opts.pylint and not opts.pep8 and not opts.pyflakes:
        run_pep8(opts.file)
        run_pyflakes(opts.file)
        run_pylint(opts.file)
    else:
        if opts.pylint:
            run_pylint(opts.file)
        if opts.pep8:
            run_pep8(opts.file)
        if opts.pyflakes:
            run_pyflakes(opts.file)

if __name__ == '__main__':
    main()
