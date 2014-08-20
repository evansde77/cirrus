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

from cirrus.environment import cirrus_home
from cirrus.configuration import load_configuration, get_pypi_auth
from fabric.operations import local


def main():
    """
    _main_

    Execute the build in the current package context.

    - reads the config to check for custom build parameters
      - defaults to ./venv for virtualenv
      - defaults to ./requirements.txt for reqs
    - builds the virtualenv
    - pip installs the requirements into it

    """
    working_dir = os.getcwd()
    config = load_configuration()
    build_params = config.get('build', {})


    # we have custom build controls in the cirrus.conf
    venv_name = build_params.get('virtualenv_name', 'venv')
    reqs_name = build_params.get('requirements_file', 'requirements.txt')
    venv_path = os.path.join(working_dir, venv_name)
    venv_bin_path = os.path.join(venv_path, 'bin', 'python')
    venv_command = os.path.join(cirrus_home(), 'cirrus', 'venv', 'bin', 'virtualenv')
    if not os.path.exists(venv_bin_path):
        cmd = "{0} --distribute {1}".format(venv_command, venv_path)
        print "Bootstrapping virtualenv: {0}".format(venv_path)
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
        print(msg)
        sys.exit(1)


if __name__ == '__main__':
    main()

