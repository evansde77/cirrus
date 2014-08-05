#!/usr/bin/env python
"""
harnesses

Common/reusable test harnesses

"""


import os
import unittest
import tempfile
import mock
import ConfigParser

from cirrus.configuration import Configuration


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
    for section, settings in sections.iteritems():
        parser.add_section(section)
        for key, value in settings.iteritems():
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
    def __init__(self, module_symbol, config_file, **settings):
        self.module_symbol = module_symbol
        self.config_file = config_file

    def setUp(self):
        self.mock_config = mock.patch(self.module_symbol)
        self.load_mock = self.mock_config.start()
        self.config = Configuration(self.config_file)
        self.config.load()
        self.load_mock.return_value = self.config

    def tearDown(self):
        self.mock_config.stop()
