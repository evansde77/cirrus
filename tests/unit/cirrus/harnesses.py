#!/usr/bin/env python
"""
harnesses

Common/reusable test harnesses

"""


import os
import unittest
import tempfile
import mock
import subprocess
from cirrus._2to3 import ConfigParser, to_str

from cirrus.configuration import Configuration


def _repo_directory():
    command = ['git', 'rev-parse', '--show-toplevel']
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    outp, err = process.communicate()
    return to_str(outp.strip())


def write_cirrus_conf(config_file, **sections):
    """
    _write_cirrus_conf_

    Util to create a cirrus configuration file and populate it
    with the settings for the package, gitflow, pypi etc sections.

    sections should be nested dict of the form {sectionname: {sectionsettings}}

    Eg:

    settings={'package': {'name': 'package_name'} }

    """
    parser = ConfigParser.RawConfigParser()
    for section, settings in iter(sections.items()):
        parser.add_section(section)
        for key, value in iter(settings.items()):
            parser.set(section, key, value)

    with open(config_file, 'w') as handle:
        parser.write(handle)


class CirrusConfigurationHarness(object):
    """
    CirrusConfigurationHarness

    Test harness that generates a mock for load_configuration in the
    module that is being mocked.

    TODO: better location for this, plus maybe combine with
       generating the cirrus config file
    """
    def __init__(self, module_symbol, config_file, gitconf_content=None, **settings):
        self.module_symbol = module_symbol
        self.config_file = config_file
        self.gitconf_str = gitconf_content
        if self.gitconf_str is None:
            self.gitconf_str = "cirrus.credential-plugin=default"

    def setUp(self):
        self.patch_environ = mock.patch.dict(os.environ, {'HOME': 'womp'})
        self.patch_environ.start()
        self.mock_config = mock.patch(self.module_symbol)
        self.load_mock = self.mock_config.start()
        self.patch_gitconfig = mock.patch('cirrus.gitconfig.shell_command')
        self.mock_gitconfig = self.patch_gitconfig.start()
        self.mock_gitconfig.return_value = self.gitconf_str
        self.config = Configuration(self.config_file)
        self.config.load()
        self.load_mock.return_value = self.config

    def tearDown(self):
        self.patch_environ.stop()
        self.mock_config.stop()
        self.patch_gitconfig.stop()
