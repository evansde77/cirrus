'''
_quality_control_

Command to run quality control via pylint, pep8, pyflakes
'''
import sys
import pluggage

from argparse import ArgumentParser

from cirrus.git_tools import get_diff_files
from cirrus.configuration import load_configuration
from cirrus.logger import get_logger

LOGGER = get_logger()

FACTORY = pluggage.registry.get_factory(
    'linter',
    load_modules=['cirrus.plugins.linters']
)


def list_plugins():
    return [
        k for k in FACTORY.registry.keys()
        if k != "LinterPlugin"
    ]


def build_parser(argslist, qc_conf):
    """
    _build_parser_

    Set up command line parser for the qc command

    """
    parser = ArgumentParser(
        description=(
            'git cirrus qc command: runs pep8, pylint, and pyflakes'
            'on source code and generates an acceptance code'
        )
    )
    parser.add_argument('qc', nargs='?')
    parser.add_argument(
        '--include-files', '-f',
        dest='include_files',
        nargs='+',
        required=False,
        default=qc_conf.get('include_files', None),
        help='specify files to run qc on, as list, supports globs')
    parser.add_argument(
        '--linters',
        nargs='+',
        default=qc_conf.get('linters', []),
        choices=list_plugins()
    )
    parser.add_argument(
        '--exclude-dirs',
        nargs='+',
        default=qc_conf.get('exclude_dirs', None)
    )
    parser.add_argument(
        '--exclude-files',
        nargs='+',
        default=qc_conf.get('exclude_files', None)
    )

    parser.add_argument(
        '--only-changes',
        action='store_true',
        help='Only run quality control on files with git changes'
    )
    parser.add_argument(
        '--test-only',
        action='store_true',
        help='print files that will be checked, dont actually check',
        default=False
    )
    parser.add_argument('-v', '--verbose', action='store_true')
    opts = parser.parse_args(argslist)
    return opts


def run_linters(opts, cirrus_conf, qc_conf):
    """
    run the linter plugins

    """
    results = {}
    known_linters = list_plugins()
    for linter in opts.linters:
        if linter not in known_linters:
            msg = "Unable to find linter plugin matching {}".format(linter)
            msg += "Valid Linters are {}".format(known_linters)
            LOGGER.error(msg)
            raise RuntimeError(msg)
        results[linter] = True
        linstance = FACTORY(linter)
        linstance.test_mode = opts.test_only
        linstance.check(opts)
        if linstance.errors:
            results['linter'] = False

    if not all(results.values()):
        failed = [k for k, v in results.items() if v]
        raise RuntimeError(
            "Failures in Quality Control Checks: {}".format(",".join(failed))
        )


def main():
    """
    _main_

    Execute test command
    """
    cirrus_conf = load_configuration()
    qc_conf = cirrus_conf.quality_control()
    opts = build_parser(sys.argv, qc_conf)
    if opts.only_changes:
        files = get_diff_files(None)
        # we only want python modules
        for item in files[:]:
            if not item.endswith('.py'):
                files.remove(item)
        if not files:
            LOGGER.info("No modules have been changed.")
            sys.exit(0)
        opts.include_files = files
    run_linters(opts, cirrus_conf, qc_conf)


if __name__ == '__main__':
    main()
