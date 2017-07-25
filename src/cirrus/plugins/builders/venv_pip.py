#!/usr/bin/env python
"""
_venv_pip_


Virtualenv & Pip based python runtime builder

"""
import os

from cirrus.builder_plugin import Builder
from cirrus.logger import get_logger
from cirrus.invoke_helpers import local
from cirrus.pypirc import build_pip_command
from virtualenvapi.manage import VirtualEnvironment


LOGGER = get_logger()


class VirtualenvPip(Builder):
    """
    Builder Plugin that uses VirtualEnv and Pip to
    create a development environment and install dependencies

    """
    def __init__(self):
        super(VirtualenvPip, self).__init__()
        self.use_sitepackages = self.build_config.get('sitepackages', False)
        self.plugin_parser.add_argument(
            '--system-site-packages',
            help='use system python site packages in virtualenv',
            default=False,
            action='store_true'
        )

    def create(self, **kwargs):
        """
        build the virtualenv
        """
        clean = kwargs.get('clean', False)
        if clean:
            self.clean(**kwargs)

        site_packages = kwargs.get('system-site-packages', self.use_sitepackages)
        upgrade = kwargs.get('upgrade', False)
        nosetupdevelop = kwargs.get('nosetupdevelop', False)
        venv = VirtualEnvironment(
            self.venv_path,
            python=self.python_bin,
            system_site_packages=site_packages
        )
        LOGGER.info("Bootstrapping virtualenv: {}".format(self.venv_path))

        venv.open_or_create()
        cmd = build_pip_command(
            self.config,
            self.venv_path,
            self.reqs_name,
            upgrade=upgrade
        )

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
            ).format(ex, cmd, self.working_dir, self.venv_path, self.reqs_name)
            LOGGER.error(msg)
            raise

        for req in self.extra_reqs:
            cmd = build_pip_command(
                self.config,
                self.venv_path,
                req,
                upgrade=upgrade
            )
            LOGGER.info("Installing extra requirements... {}".format(cmd))
            try:
                local(cmd)
            except OSError as ex:
                msg = (
                    "Error running pip install command extra "
                    "requirements install: {}\n{}"
                ).format(req, ex)
                LOGGER.error(msg)
                raise
        # setup for development
        if nosetupdevelop:
            msg = "skipping python setup.py develop..."
            LOGGER.info(msg)
        else:
            self.run_setup_develop()

    def clean(self, **kwargs):
        if os.path.exists(self.venv_path):
            cmd = "rm -rf {0}".format(self.venv_path)
            LOGGER.info("Removing virtualenv: {0}".format(self.venv_path))
            local(cmd)

    def activate(self):
        command = ". {}/bin/activate".format(self.venv_path)
        return command
