#!/usr/bin/env python
"""
builder plugin

Define the plugin base API for builders
for managing virtualenvs of various flavours

"""
import os
import re
import argparse

from cirrus.configuration import load_configuration
from cirrus.environment import repo_directory

from pluggage.factory_plugin import PluggagePlugin
from cirrus.logger import get_logger
from cirrus.invoke_helpers import local

LOGGER = get_logger()


CONDA_VERSION_FORMAT = re.compile('^[0-9]{1}\.[0-9]{1}$')
PYTHON_VERSION_FORMAT = re.compile('^python[0-9]{1}\.[0-9]{1}$')


def normalise_version(v):
    if v is None:
        return None
    result = str(v)
    if CONDA_VERSION_FORMAT.match(str(v)):
        result = 'python{}'.format(v)
    if not PYTHON_VERSION_FORMAT.match(result):
        msg = (
            "Unable to reconcile python version from cirrus.conf build section:\n"
            "Value in cirrus.conf [build]: python={v}\n"
            "Expected either pythonX.Y or X.Y format"
        )
        LOGGER.error(msg)
        raise RuntimeError(msg)
    return result


def py_version_to_conda(v):
    return v.replace('python', '')


def conda_version_to_py(v):
    return 'python{}'.format(v)


class Builder(PluggagePlugin):
    PLUGGAGE_FACTORY_NAME = 'builder'

    def __init__(self):
        super(Builder, self).__init__()
        self.plugin_parser = argparse.ArgumentParser()
        self.config = load_configuration()
        self.build_config = self.config.get('build', {})
        self.working_dir = repo_directory()
        self.venv_name = self.build_config.get('virtualenv_name', 'venv')
        self.reqs_name = self.build_config.get('requirements_file', 'requirements.txt')
        self.extra_reqs = self.build_config.get('extra_requirements', [])
        self.python_bin = self.build_config.get('python', None)
        self.extra_reqs = self.str_to_list(self.extra_reqs)
        self.venv_path = os.path.join(self.working_dir, self.venv_name)

    def process_extra_args(self, extras):
        opts, _ = self.plugin_parser.parse_known_args(extras)
        return vars(opts)

    def create(self, **kwargs):
        """
        _create_

        create a new python runtime environment
        at the location provided

        """
        pass

    def clean(self, **kwargs):
        """
        _clean_

        remove the specified runtime environment

        """
        pass

    def activate(self):
        """
        return a shell command string to activate the
        runtime environment
        """
        pass

    def run_setup_develop(self):
        LOGGER.info("Running setup.py develop...")
        activate = self.activate()
        local(
            '{} && python setup.py develop'.format(
                activate
            )
        )

    @property
    def python_bin_for_venv(self):
        if not self.python_bin:
            return self.python_bin
        v = normalise_version(self.python_bin)
        return v

    @property
    def python_bin_for_conda(self):
        if not self.python_bin:
            return self.python_bin
        v = normalise_version(self.python_bin)
        return py_version_to_conda(v)

    @classmethod
    def str_to_list(cls, s, delim=','):
        if isinstance(s, list):
            return s
        if delim in s:
            return [x.strip() for x in s.split(delim) if x.strip()]
        return [s]
