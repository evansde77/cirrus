#!/usr/bin/env python
"""
tests for configuration module
"""
import os
import unittest
import ConfigParser
import tempfile
import mock

from cirrus.plugins.creds.default import Default
from cirrus.configuration import load_configuration


class ConfigurationTests(unittest.TestCase):
    """
    tests for cirrus.conf interface class

    """
    def setUp(self):
        """create a sample conf file"""
        self.dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.dir, 'cirrus.conf')
        self.gitconfig = os.path.join(self.dir, '.gitconfig')

        parser = ConfigParser.RawConfigParser()
        parser.add_section('package')
        parser.add_section('gitflow')
        parser.set('package', 'name', 'cirrus_tests')
        parser.set('package', 'version', '1.2.3')
        parser.set('gitflow', 'develop_branch', 'develop')
        parser.set('gitflow', 'release_branch_prefix', 'release/')
        parser.set('gitflow', 'feature_branch_prefix', 'feature/')

        with open(self.test_file, 'w') as handle:
            parser.write(handle)

        gitconf = ConfigParser.RawConfigParser()
        gitconf.add_section('cirrus')
        gitconf.set('cirrus', 'credential-plugin', 'default')
        with open(self.gitconfig, 'w') as handle:
            gitconf.write(handle)

        self.patcher = mock.patch('cirrus.plugins.creds.default.os')
        default_os = self.patcher.start()
        default_os.path = mock.Mock()
        default_os.path.join = mock.Mock()
        default_os.path.join.return_value = self.gitconfig

    def tearDown(self):
        """cleanup"""
        self.patcher.stop()
        if os.path.exists(self.dir):
            os.system('rm -rf {0}'.format(self.dir))

    def test_reading(self):
        """test config load """
        #test read and accessors
        config = load_configuration(package_dir=self.dir, gitconfig_file=self.gitconfig)
        self.assertEqual(config.package_version(), '1.2.3')
        self.assertEqual(config.package_name(), 'cirrus_tests')

        self.assertEqual(config.gitflow_branch_name(), 'develop')
        self.assertEqual(config.gitflow_release_prefix(), 'release/')
        self.assertEqual(config.gitflow_feature_prefix(), 'feature/')

        self.assertEqual(config.release_notes(), (None, None))
        self.assertEqual(config.version_file(), (None, '__version__'))

        self.failUnless(config.credentials is not None)
        self.failUnless(isinstance(config.credentials, Default))

        # test updating version
        config.update_package_version('1.2.4')
        self.assertEqual(config.package_version(), '1.2.4')
        config2 = load_configuration(package_dir=self.dir)
        self.assertEqual(config2.package_version(), '1.2.4')

    @mock.patch('cirrus.configuration.subprocess.Popen')
    def test_reading_missing(self, mock_pop):
        """test config load using repo dir"""
        mock_result = mock.Mock()
        mock_result.communicate = mock.Mock()
        mock_result.communicate.return_value = (self.dir, None)
        mock_pop.return_value = mock_result
        config = load_configuration(package_dir="womp")

        self.failUnless(mock_result.communicate.called)
        mock_pop.assert_has_calls(mock.call(['git', 'rev-parse', '--show-toplevel'], stdout=-1))
        self.assertEqual(config.package_version(), '1.2.3')
        self.assertEqual(config.package_name(), 'cirrus_tests')

    def test_configuration_map(self):
        """test building config mapping"""
        config = load_configuration(package_dir=self.dir, gitconfig_file=self.gitconfig)
        mapping = config.configuration_map()
        self.failUnless('cirrus' in mapping)
        self.failUnless('credentials' in mapping['cirrus'])
        self.failUnless('configuration' in mapping['cirrus'])
        self.failUnless('github_credentials' in mapping['cirrus']['credentials'])
        self.assertEqual(
            mapping['cirrus']['credentials']['github_credentials'],
            {'github_user': None, 'github_token': None}
        )




if __name__ == '__main__':
    unittest.main()