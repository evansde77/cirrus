#!/usr/bin/env python
import os
from cirrus.builder_plugin import Builder
from cirrus.logger import get_logger
from cirrus.invoke_helpers import local


LOGGER = get_logger()


class CondaEnv(Builder):

    def __init__(self):
        super(CondaEnv, self).__init__()
        self.conda_bin = 'conda'
        self.plugin_parser.add_argument(
            '--conda',
            help='conda binary to use if different from default conda',
            default='conda'
        )
        self.plugin_parser.add_argument(
            '--environment',
            help='conda environment file to process',
            default=None
        )

    def create(self, **kwargs):
        python_bin = kwargs.get("python", self.python_bin)
        conda = kwargs.get('conda', self.conda_bin)
        upgrade = kwargs.get('upgrade', False)
        nosetupdevelop = kwargs.get('nosetupdevelop', False)
        environment = kwargs.get('environment', None)
        if environment is None:
            environment = self.build_config.get('conda-environment', None)
        if environment is None:
            msg = "No conda environment yaml specified in cirrus.conf [build] section or via --environment option"
            LOGGER.error(msg)
            raise RuntimeError(msg)
        clean = kwargs.get('clean', False)
        if clean:
            self.clean(**kwargs)

        venv_command = "{} env create -f {} -p {} ".format(
            conda,
            environment,
            self.venv_path
        )
        if python_bin:
            # should probably check this is int or int.int format
            venv_command += " python={}".format(self.python_bin)

        if not os.path.exists(self.venv_path):
            LOGGER.info("Bootstrapping conda env: {0}".format(self.venv_path))
            local(venv_command)

        if upgrade:
            cmd = "{activate} && conda env update {venv} -f {env}".format(
                activate=self.activate(),
                venv=self.venv_path,
                env=environment
            )
            try:
                local(cmd)
            except OSError as ex:
                msg = (
                    "Error running conda env update command during build\n"
                    "Error was {0}\n"
                    "Running command: {1}\n"
                    "Working Dir: {2}\n"
                    "Conda env: {3}\n"
                    "Requirements: {4}\n"
                ).format(ex, cmd, self.working_dir, self.venv_path, self.reqs_name)
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
