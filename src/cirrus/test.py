'''
_test_

Command to run available test suites in a package
'''
import sys

from fabric.operations import local
from argparse import ArgumentParser

from cirrus.git_tools import get_diff_files
from cirrus.configuration import load_configuration
from cirrus.logger import get_logger

LOGGER = get_logger()


def build_parser(argslist):
    """
    _build_parser_

    Set up command line parser for the release command

    """
    parser = ArgumentParser(
        description='git cirrus test command'
    )
    parser.add_argument('test', nargs='?')
    parser.add_argument('-s', '--suite', dest='suite')
    parser.add_argument(
        '--only-changes',
        action='store_true',
        help='Only run nose on packages that you are working on')

    opts = parser.parse_args(argslist)

    if opts.only_changes and opts.suite is not None:
        raise("Cannot set '--only-changes=True' and provide a suite")

    return opts


def nose_test(opts):
    """
    _nose_test_

    Locally activate vitrualenv and run tests
    """
    config = load_configuration()
    nose_options = ''
    if opts.only_changes:
        files = get_diff_files(None)
        #we only want python modules
        for item in files:
            if not item.endswith('.py'):
                files.remove(item)
        if not files:
            LOGGER.info("No modules have been changed.")
            exit(0)
        nose_options = ' '.join(files)
    elif opts.suite is not None:
        nose_options = '-w {0}'.format(config.test_where(opts.suite))
    else:
        nose_options = '-w {0}'.format(config.test_where('default'))

    local('. ./{0}/bin/activate && nosetests {1}'.format(
        config.venv_name(),
        nose_options))


def main():
    """
    _main_

    Execute test command
    """
    opts = build_parser(sys.argv)
    nose_test(opts)


if __name__ == '__main__':
    main()
