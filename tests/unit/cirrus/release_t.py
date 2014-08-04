#!/usr/bin/env python
"""
release command tests

"""
import os
import unittest
import tempfile
import mock
import ConfigParser

from cirrus.release import new_release
from cirrus.configuration import Configuration


def write_cirrus_conf(config_file, package, gitflow):
    """
    _write_cirrus_conf_

    Util to create a cirrus configuration file and populate it
    with the settings for the package and gitflow section.

    TODO: better location

    """
    parser = ConfigParser.RawConfigParser()
    parser.add_section('package')
    parser.add_section('gitflow')
    for key, value in package.iteritems():
        parser.set('package', key, value)
    for key, value in gitflow.iteritems():
        parser.set('gitflow', key, value)

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
    def __init__(self, module_symbol, config_file, package=dict(), github=dict() ):
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


class ReleaseNewCommandTest(unittest.TestCase):
    """
    Test Case for new_release function
    """
    def setUp(self):
        """set up test files"""
        self.dir = tempfile.mkdtemp()
        self.config = os.path.join(self.dir, 'cirrus.conf')
        write_cirrus_conf(self.config,
            {'name': 'cirrus_unittest', 'version': '1.2.3'},
            {'develop_branch': 'develop', 'release_branch_prefix': 'release/'}
            )
        self.harness = CirrusConfigurationHarness('cirrus.release.load_configuration', self.config)
        self.harness.setUp()
        self.patch_pull = mock.patch('cirrus.release.checkout_and_pull')
        self.patch_branch = mock.patch('cirrus.release.branch')
        self.patch_commit = mock.patch('cirrus.release.commit_files')
        self.mock_pull = self.patch_pull.start()
        self.mock_branch = self.patch_branch.start()
        self.mock_commit = self.patch_commit.start()

    def tearDown(self):
        self.patch_pull.stop()
        self.patch_branch.stop()
        self.patch_commit.stop()
        self.harness.tearDown()
        if os.path.exists(self.dir):
            os.system('rm -rf {0}'.format(self.dir))


    def test_new_release(self):
        """
        _test_new_release_

        """
        opts = mock.Mock()
        opts.micro = True
        opts.major = False
        opts.minor = False

        # should create a new minor release, editing
        # the cirrus config in the test dir
        new_release(opts)

        # verify new version
        new_conf = Configuration(self.config)
        new_conf.load()
        self.assertEqual(new_conf.package_version(), '1.2.4')

        self.failUnless(self.mock_pull.called)
        self.assertEqual(self.mock_pull.call_args[0][1], 'develop')
        self.failUnless(self.mock_branch.called)
        self.assertEqual(self.mock_branch.call_args[0][1], 'release/1.2.4')
        self.failUnless(self.mock_commit.called)
        self.assertEqual(self.mock_commit.call_args[0][2], 'cirrus.conf')



if __name__ == '__main__':
    unittest.main()
