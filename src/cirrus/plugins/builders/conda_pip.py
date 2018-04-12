#!/usr/bin/env python

import os
from cirrus.builder_plugin import Builder
from cirrus.logger import get_logger
from cirrus.invoke_helpers import local
from cirrus.pypirc import build_pip_command
from cirrus.conda_utils import is_anaconda_5, find_conda_setup_script

LOGGER = get_logger()


class CondaPip(Builder):

    def __init__(self):
        super(CondaPip, self).__init__()
        self.conda_bin = 'conda'
        self.plugin_parser.add_argument(
            '--conda',
            help='conda binary to use if different from default conda',
            default='conda'
        )

    def create(self, **kwargs):
        python_bin = kwargs.get("python")
        if python_bin is not None:
            self.python_bin = python_bin
            LOGGER.info("Overriding python bin from command line: {}".format(python_bin))
        conda = kwargs.get('conda', self.conda_bin)
        upgrade = kwargs.get('upgrade', False)
        nosetupdevelop = kwargs.get('nosetupdevelop', False)
        clean = kwargs.get('clean', False)
        if clean:
            self.clean(**kwargs)

        venv_command = "{} create -y -m -p {} pip virtualenv".format(
            conda,
            self.venv_path
        )
        if self.python_bin:
            LOGGER.info("using python bin: {}".format(self.python_bin_for_conda))
            # should probably check this is int or int.int format
            venv_command += " python={}".format(self.python_bin_for_conda)

        if not os.path.exists(self.venv_path):
            LOGGER.info("Bootstrapping conda env: {0}".format(self.venv_path))
            local(venv_command)

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
                "Conda env: {3}\n"
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
        conda = kwargs.get('conda', self.conda_bin)
        if os.path.exists(self.venv_path):
            cmd = "{} remove --all -y -p {}".format(
                conda,
                self.venv_path
            )
            LOGGER.info("Removing existing conda env: {0}".format(self.venv_path))
            local(cmd)

    def activate(self):
        cmd = 'source'
        if is_anaconda_5():
            setup = find_conda_setup_script()
            if setup:
                cmd = " . {} && conda ".format(setup)
            else:
                cmd = "conda"

        activate_script = '{}/bin/activate'.format(self.venv_path)
        if os.path.exists(activate_script):
            command = "{} {}/bin/activate {}".format(cmd, self.venv_path, self.venv_path)
        else:
            command = "{} activate {}".format(cmd, self.venv_path)
        return command
