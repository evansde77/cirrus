#!/usr/bin/env python
"""
builder plugin

Define the plugin base API for builders
for managing virtualenvs of various flavours

"""
import os
import argparse

from cirrus.configuration import load_configuration
from cirrus.environment import repo_directory

from pluggage.factory_plugin import PluggagePlugin
from cirrus.logger import get_logger
from cirrus.invoke_helpers import local

LOGGER = get_logger()


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

    @classmethod
    def str_to_list(cls, s, delim=','):
        if isinstance(s, list):
            return s
        if delim in s:
            return [x.strip() for x in s.split(delim) if x.strip()]
        return [s]