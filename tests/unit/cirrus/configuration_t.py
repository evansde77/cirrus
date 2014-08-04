#!/usr/bin/env python
"""
tests for configuration module
"""
import os
import unittest
import ConfigParser
import tempfile

from cirrus.configuration import load_configuration


class ConfigurationTests(unittest.TestCase):
    """
    tests for cirrus.conf interface class

    """
    def setUp(self):
        """create a sample conf file"""
        self.dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.dir, 'cirrus.conf')

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

    def tearDown(self):
        """cleanup"""
        if os.path.exists(self.dir):
            os.system('rm -rf {0}'.format(self.dir))


    def test_reading(self):
        """test config load """
        #test read and accessors
        config = load_configuration(package_dir=self.dir)
        self.assertEqual(config.package_version(), '1.2.3')
        self.assertEqual(config.package_name(), 'cirrus_tests')

        self.assertEqual(config.gitflow_branch_name(), 'develop')
        self.assertEqual(config.gitflow_release_prefix(), 'release/')
        self.assertEqual(config.gitflow_feature_prefix(), 'feature/')

        self.assertEqual(config.release_notes(), (None, None))
        self.assertEqual(config.version_file(), (None, '__version__'))

        # test updating version
        config.update_package_version('1.2.4')
        self.assertEqual(config.package_version(), '1.2.4')
        config2 = load_configuration(package_dir=self.dir)
        self.assertEqual(config2.package_version(), '1.2.4')

if __name__ == '__main__':
    unittest.main()