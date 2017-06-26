#!/usr/bin/env python
"""
tests for default credential manager using gitconfig
"""
import os
import unittest
import tempfile

from cirrus.plugins.creds.default import Default
from cirrus._2to3 import ConfigParser

class DefaultCredsTests(unittest.TestCase):
    """
    test default plugin gitconfig access
    """
    def setUp(self):
        """set up a test gitconfig"""
        self.dir = tempfile.mkdtemp()
        self.gitconfig = os.path.join(self.dir, '.gitconfig')

        gitconf = ConfigParser.RawConfigParser()
        gitconf.add_section('cirrus')
        gitconf.set('cirrus', 'credential-plugin', 'default')
        gitconf.set('cirrus', 'github-user', 'steve')
        gitconf.set('cirrus', 'github-token', 'steves token')

        with open(self.gitconfig, 'w') as handle:
            gitconf.write(handle)

    def tearDown(self):
        """cleanup"""
        if os.path.exists(self.dir):
            os.system('rm -rf {0}'.format(self.dir))

    def test_reading_gitconfig(self):
        """test reading in the fake gitconfig and accessing data"""
        plugin = Default(gitconfig_file=self.gitconfig)
        gh = plugin.github_credentials()
        self.failUnless('github_user' in gh)
        self.failUnless('github_token' in gh)
        self.assertEqual(gh['github_user'], 'steve')
        self.assertEqual(gh['github_token'], 'steves token')

        # test all the methods work with defaults
        for n, m in plugin.credential_methods():
            m()


if __name__ == '__main__':
    unittest.main()
