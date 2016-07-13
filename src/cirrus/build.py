#!/usr/bin/env python
"""
_build_

Implements the cirrus build command.

This command:
 - creates a virtualenv in the package
 - pip installs requirements.txt for the package into the venv

"""
import os
import sys
from argparse import ArgumentParser

from cirrus.documentation_utils import build_docs
from cirrus.environment import cirrus_home
from cirrus.configuration import load_configuration, get_pypi_auth
from cirrus.logger import get_logger
from fabric.operations import local

LOGGER = get_logger()


def build_parser(argslist):
    """
    _build_parser_

    Set up command line parser for the build command

    : param list argslist: A list of command line arguments
    """
    parser = ArgumentParser(
        description='git cirrus build'
    )
    parser.add_argument('command', nargs='?')
    parser.add_argument(
        '-c',
        '--clean',
        action='store_true',
        help='remove existing virtual environment')

    parser.add_argument(
        '-d',
        '--docs',
        nargs='*',
        help='generate documentation with Sphinx (Makefile path must be set in cirrus.conf.')

    parser.add_argument(
        '-u',
        '--upgrade',
        action='store_true',
        default=False,
        help='Use --upgrade to update the dependencies in the package requirements'
    )
    opts = parser.parse_args(argslist)
    return opts


def execute_build(opts):
    """
    _execute_build_

    Execute the build in the current package context.

    - reads the config to check for custom build parameters
      - defaults to ./venv for virtualenv
      - defaults to ./requirements.txt for reqs
    - removes existing virtualenv if clean flag is set
    - builds the virtualenv
    - pip installs the requirements into it

    : param argparse.Namspace opts: A Namespace of build options
    """
    working_dir = os.getcwd()
    config = load_configuration()
    build_params = config.get('build', {})

    # we have custom build controls in the cirrus.conf
    venv_name = build_params.get('virtualenv_name', 'venv')
    reqs_name = build_params.get('requirements_file', 'requirements.txt')
    venv_path = os.path.join(working_dir, venv_name)
    venv_bin_path = os.path.join(venv_path, 'bin', 'python')
    venv_command = os.path.join(
        cirrus_home(),
        'venv',
        'bin',
        'virtualenv')

    # remove existing virtual env if building clean
    if opts.clean and os.path.exists(venv_path):
        cmd = "rm -rf {0}".format(venv_path)
        print "Removing existing virtualenv: {0}".format(venv_path)
        local(cmd)

    if not os.path.exists(venv_bin_path):
        cmd = "{0} {1}".format(venv_command, venv_path)
        LOGGER.info("Bootstrapping virtualenv: {0}".format(venv_path))
        local(cmd)

    # custom pypi server
    pypi_server = config.pypi_url()
    if pypi_server is not None:
        pypi_conf = get_pypi_auth()
        pypi_url = "https://{pypi_username}:{pypi_token}@{pypi_server}/simple".format(
            pypi_token=pypi_conf['token'],
            pypi_username=pypi_conf['username'],
            pypi_server=pypi_server
        )
        if opts.upgrade:
            cmd = (
                '{0}/bin/pip install --upgrade '
                "-i {1} "
                '-r {2}'
                ).format(venv_path, pypi_url, reqs_name)
        else:
            cmd = (
                '{0}/bin/pip install '
                "-i {1} "
                '-r {2}'
                ).format(venv_path, pypi_url, reqs_name)

    else:
        # no pypi server
        if opts.upgrade:
            cmd = '{0}/bin/pip install --upgrade -r {1}'.format(venv_path, reqs_name)
        else:
            cmd = '{0}/bin/pip install -r {1}'.format(venv_path, reqs_name)

    try:
        local(cmd)
    except OSError as ex:
        msg = (
            "Error running pip install command during build\n"
            "Error was {0}\n"
            "Running command: {1}\n"
            "Working Dir: {2}\n"
            "Virtualenv: {3}\n"
            "Requirements: {4}\n"
            ).format(ex, cmd, working_dir, venv_path, reqs_name)
        LOGGER.info(msg)
        sys.exit(1)

    # setup for development
    local('. ./{0}/bin/activate && python setup.py develop'.format(venv_name))


def main():
    """
    _main_

    Execute build command
    """
    opts = build_parser(sys.argv)
    execute_build(opts)

    if opts.docs is not None:
        build_docs(make_opts=opts.docs)


if __name__ == '__main__':
    main()
