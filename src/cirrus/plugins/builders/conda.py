#!/usr/bin/env python

import os
from cirrus.builder_plugin import Builder
from cirrus.logger import get_logger
from cirrus.invoke_helpers import local


LOGGER = get_logger()


class Conda(Builder):

    def __init__(self):
        super(Conda, self).__init__()
        self.conda_bin = 'conda'
        self.plugin_parser.add_argument(
            '--conda',
            help='conda binary to use if different from default conda',
            default='conda'
        )
        self.plugin_parser.add_argument(
            '--conda-channels',
            nargs='+',
            help='space separated list of conda channels',
            default=[]

        )

    def create(self, **kwargs):
        python_bin = kwargs.get("python", self.python_bin)
        conda = kwargs.get('conda', self.conda_bin)
        upgrade = kwargs.get('upgrade', False)
        nosetupdevelop = kwargs.get('nosetupdevelop', False)
        clean = kwargs.get('clean', False)
        channels = self.str_to_list(self.build_config.get('conda_channels', []))
        LOGGER.info("channels from conf: {}".format(channels))
        if kwargs.get('conda_channels'):
            channels = kwargs['conda_channels']
        if clean:
            self.clean(**kwargs)

        channels = ''.join(' -c {}'.format(c) for c in channels)
        LOGGER.info("channels: result={}".format(kwargs.get('conda_channels'), self.build_config.get('conda_channels'), channels))
        venv_command = "{} create -y -m {} -p {} pip virtualenv".format(
            conda,
            channels,
            self.venv_path
        )
        if python_bin:
            # should probably check this is int or int.int format
            venv_command += " python={}".format(self.python_bin)

        if not os.path.exists(self.venv_path):
            LOGGER.info("Bootstrapping conda env: {0}".format(self.venv_path))
            local(venv_command)

        cmd = "conda install {} {} --yes --file {}".format(
            '--update-dependencies' if upgrade else '--no-update-dependencies',
            channels,
            self.reqs_name
        )
        try:
            local(cmd)
        except OSError as ex:
            msg = (
                "Error running conda install command during build\n"
                "Error was {0}\n"
                "Running command: {1}\n"
                "Working Dir: {2}\n"
                "Conda env: {3}\n"
                "Requirements: {4}\n"
            ).format(ex, cmd, self.working_dir, self.venv_path, self.reqs_name)
            LOGGER.error(msg)
            raise

        for req in self.extra_reqs:
            cmd = "conda install {} {} --yes --file {}".format(
                '--update-dependencies' if upgrade else '',
                channels,
                req
            )
            LOGGER.info("Installing extra requirements... {}".format(cmd))
            try:
                local(cmd)
            except OSError as ex:
                msg = (
                    "Error running conda install command extra "
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
        command = "source {}/bin/activate {}".format(self.venv_path, self.venv_path)
        return command
