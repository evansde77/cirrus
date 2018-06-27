#!/usr/bin/env python
"""
tests for configuration module
"""
import os
import unittest
import tempfile
import mock

from cirrus.plugins.creds.default import Default
from cirrus.configuration import load_configuration
from cirrus._2to3 import ConfigParser


class ConfigurationTests(unittest.TestCase):
    """
    tests for cirrus.conf interface class

    """
    def setUp(self):
        """create a sample conf file"""
        self.dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.dir, 'cirrus.conf')
        self.gitconfig = os.path.join(self.dir, '.gitconfig')
        self.patch_env = mock.patch.dict(
            os.environ,
            {'HOME': self.dir, 'USER': 'unittests'}
        )
        self.patch_env.start()

        parser = ConfigParser.RawConfigParser()
        parser.add_section('package')
        parser.add_section('gitflow')
        parser.add_section('extras_require')
        parser.set('package', 'name', 'cirrus_tests')
        parser.set('package', 'version', '1.2.3')
        parser.set('gitflow', 'develop_branch', 'develop')
        parser.set('gitflow', 'release_branch_prefix', 'release/')
        parser.set('gitflow', 'feature_branch_prefix', 'feature/')
        parser.set('extras_require', 'analysis', 'pandas;scipy')
        parser.set('extras_require', 'server', 'Flask==0.0.0')

        with open(self.test_file, 'w') as handle:
            parser.write(handle)

        gitconf = ConfigParser.RawConfigParser()
        gitconf.add_section('cirrus')
        gitconf.set('cirrus', 'credential-plugin', 'default')
        with open(self.gitconfig, 'w') as handle:
            gitconf.write(handle)

        self.gitconf_str = "cirrus.credential-plugin=default"

        self.patcher = mock.patch('cirrus.plugins.creds.default.os')
        default_os = self.patcher.start()
        default_os.path = mock.Mock()
        default_os.path.join = mock.Mock()
        default_os.path.join.return_value = self.gitconfig

    def tearDown(self):
        """cleanup"""
        self.patcher.stop()
        self.patch_env.stop()
        if os.path.exists(self.dir):
            os.system('rm -rf {0}'.format(self.dir))

    @mock.patch('cirrus.gitconfig.shell_command')
    def test_reading(self, mock_shell):
        """test config load """
        #  test read and accessors
        mock_shell.return_value = self.gitconf_str
        config = load_configuration(
            package_dir=self.dir,
            gitconfig_file=self.gitconfig
        )
        self.assertEqual(config.package_version(), '1.2.3')
        self.assertEqual(config.package_name(), 'cirrus_tests')

        self.assertEqual(config.gitflow_branch_name(), 'develop')
        self.assertEqual(config.gitflow_release_prefix(), 'release/')
        self.assertEqual(config.gitflow_feature_prefix(), 'feature/')

        self.assertEqual(config.release_notes(), (None, None))
        self.assertEqual(config.version_file(), (None, '__version__'))
        self.assertEqual(
            config.extras_require(),
            {'analysis': 'pandas;scipy', 'server': 'Flask==0.0.0'}
        )

        self.assertTrue(config.credentials is not None)
        self.assertTrue(isinstance(config.credentials, Default))

        # test updating version
        config.update_package_version('1.2.4')
        self.assertEqual(config.package_version(), '1.2.4')
        config2 = load_configuration(package_dir=self.dir)
        self.assertEqual(config2.package_version(), '1.2.4')

    def test_configuration_map(self):
        """test building config mapping"""
        config = load_configuration(package_dir=self.dir, gitconfig_file=self.gitconfig)
        mapping = config.configuration_map()
        self.assertTrue('cirrus' in mapping)
        self.assertTrue('credentials' in mapping['cirrus'])
        self.assertTrue('configuration' in mapping['cirrus'])
        self.assertTrue('github_credentials' in mapping['cirrus']['credentials'])
        self.assertEqual(
            mapping['cirrus']['credentials']['github_credentials'],
            {'github_user': None, 'github_token': None}
        )
        self.assertEqual(
            mapping['cirrus']['configuration']['package']['name'], 'cirrus_tests'
        )



if __name__ == '__main__':
    unittest.main()