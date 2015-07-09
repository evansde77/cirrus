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
        '--docs',
        nargs='*',
        help='generate documentation with Sphinx (Makefile path must be set in cirrus.conf.')

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
        'cirrus',
        'venv',
        'bin',
        'virtualenv')

    # remove existing virtual env if building clean
    if opts.clean and os.path.exists(venv_path):
        cmd = "rm -rf {0}".format(venv_path)
        print "Removing existing virtualenv: {0}".format(venv_path)
        local(cmd)

    if not os.path.exists(venv_bin_path):
        cmd = "{0} --distribute {1}".format(venv_command, venv_path)
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

        cmd = (
            '{0}/bin/pip install '
            "-i {1} "
            '-r {2}'
            ).format(venv_path, pypi_url, reqs_name)

    else:
        # no pypi server
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


def build_docs(opts):
    """
    _build_docs_

    Runs 'make' against a Sphinx makefile.
    Requires the following cirrus.conf section:

    [doc]
    sphinx_makefile_dir = /path/to/makefile

    : param argparse.Namspace opts: A Namespace of build options
    """
    LOGGER.info('Building docs')
    config = load_configuration()

    try:
        docs_root = os.path.join(os.getcwd(),
                                 config['doc']['sphinx_makefile_dir'])
    except KeyError:
        LOGGER.error('Did not find a complete [doc] section in cirrus.conf'
                     '\nSee below for an example:'
                     '\n[doc]'
                     '\n;sphinx_makefile_dir = /path/to/sphinx')
        sys.exit(1)

    cmd = 'cd {} && make clean html'.format(docs_root)

    if opts.docs:
        # additional args were passed after --docs.  Pass these to make
        cmd = 'cd {} && make {}'.format(docs_root, ' '.join(opts.docs))

    local(cmd)
    LOGGER.info('Build command was "{}"'.format(cmd))


def main():
    """
    _main_

    Execute build command
    """
    opts = build_parser(sys.argv)
    execute_build(opts)

    if opts.docs is not None:
        build_docs(opts)


if __name__ == '__main__':
    main()
