#!/usr/bin/env python
"""
_build_

Implements the cirrus build command.

This command:
 - creates a virtualenv in the package
 - pip installs requirements.txt for the package into the venv

"""
import os
import subprocess
from cirrus.environment import cirrus_home
from cirrus.configuration import load_configuration


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
    venv_command = os.path.join(cirrus_home(), 'bin', 'virtualenv')
    if not os.path.exists(venv_path):
        cmd = [venv_command, '--distribute', venv_path]
        subprocess.call(cmd)

    # now we can install requirements into the newly created venv
    cmd = [
        '{0}/bin/pip'.format(venv_path),
        'install',
        '-r',
        reqs_name
    ]
    subprocess.call(cmd)


if __name__ == '__main__':
    main()

