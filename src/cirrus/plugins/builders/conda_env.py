#!/usr/bin/env python
import os
from cirrus.builder_plugin import Builder
from cirrus.logger import get_logger
from cirrus.invoke_helpers import local
from cirrus.conda_utils import is_anaconda_5, find_conda_setup_script


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
        self.plugin_parser.add_argument(
            '--extra-pip-requirements',
            dest='extra_pip',
            nargs="+",
            default=[],
            help="Extra pip requirements to install post creation of env"
        )
        self.plugin_parser.add_argument(
            '--extra-conda-requirements',
            nargs="+",
            default=[],
            dest='extra_conda',
            help="Extra conda requirements to install post env creation"
        )

    def create(self, **kwargs):
        python_bin = kwargs.get("python")
        if python_bin is not None:
            self.python_bin = python_bin
        conda = kwargs.get('conda', self.conda_bin)
        upgrade = kwargs.get('upgrade', False)
        extra_pip = self.build_config.get('extra_pip_requirements')
        if extra_pip:
            extra_pip = self.str_to_list(extra_pip)
        if kwargs.get('extra-pip-requirements'):
            extra_pip = kwargs['extra-pip-requirements']
        extra_conda = self.build_config.get('extra_conda_requirements')
        if extra_conda:
            extra_conda = self.str_to_list(extra_conda)
        if kwargs.get('extra-conda-requirements'):
            extra_conda = kwargs['extra-conda-requirements']

        # TODO: also accept this from build_config, override from cli
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
        if self.python_bin:
            # should probably check this is int or int.int format
            venv_command += " python={}".format(self.python_bin_for_conda)
            msg = (
                "Passing python version {} to conda env setup: "
                "Usually it is safer to set this in the environment yaml"
            ).format(
                self.python_bin_for_conda
            )
            LOGGER.warning(msg)

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

        if extra_conda:
            for conda_file in extra_conda:
                cmd = "{activate} && conda install {venv} -f {file}".format(
                    activate=self.activate(),
                    venv=self.venv_path,
                    file=conda_file
                )
                LOGGER.info("Installing extra conda reqs: {}".format(conda_file))
                try:
                    local(cmd)
                except OSError as ex:
                    msg = (
                        "Error running conda install extras command during build\n"
                        "Error was {0}\n"
                        "Running command: {1}\n"
                        "Working Dir: {2}\n"
                        "Conda env: {3}\n"
                        "Extra Conda Requirements: {4}\n"
                    ).format(ex, cmd, self.working_dir, self.venv_path, conda_file)
                    LOGGER.error(msg)
                    raise

        if extra_pip:
            for pip_file in extra_pip:
                pip_options = self.config.pip_options()
                cmd = "{activate} && pip install -r {reqs}".format(
                    activate=self.activate(),
                    venv=self.venv_path,
                    reqs=pip_file
                )
                if pip_options:
                    cmd += " {}".format(pip_options)
                LOGGER.info("Installing extra pip reqs {}".format(pip_file))
                try:
                    local(cmd)
                except OSError as ex:
                    msg = (
                        "Error running pip install extras command during build\n"
                        "Error was {0}\n"
                        "Running command: {1}\n"
                        "Working Dir: {2}\n"
                        "Conda env: {3}\n"
                        "Extra pip Requirements: {4}\n"
                    ).format(ex, cmd, self.working_dir, self.venv_path, pip_file)
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
