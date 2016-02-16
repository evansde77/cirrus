#!/usr/bin/env python
"""
_pypi_upload_

Upload plugin that does a pypi sdist upload

"""
import os
from fabric.operations import local

from cirrus.upload_plugins import Uploader
from cirrus.logger import get_logger

LOGGER = get_logger()


class Pypi(Uploader):
    PLUGGAGE_OBJECT_NAME = 'pypi'

    def upload(self, opts, build_artifact):
        """
        upload to pypi using sdist.
        This will use settings from the ~/.pypirc file.
        The pypi-url CLI option can be used to give a pypi
        server url or an alias specified in the pypirc
        """
        pypirc = os.path.expandvars('$HOME/.pypirc')
        if not os.path.exists(pypirc):
            msg = "$HOME/.pypirc not found, cannot upload to pypi"
            LOGGER.error(msg)
            raise RuntimeError(msg)

        command = 'python setup.py sdist upload'
        if opts.pypi_url:
            LOGGER.info("using pypi server {}".format(opts.pypi_url))
            pypi_url = opts.pypi_url
            command += ' -r {}'.format(pypi_url)
        LOGGER.info("Executing {} ...".format(command))
        local(command)
