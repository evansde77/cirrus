#!/usr/bin/env python
"""
keyring_plugin_tests

Test coverage for the keyring creds plugin
"""

import unittest
import mock
from cirrus.plugins.creds.keyring import Keyring


class KeyringCredsTest(unittest.TestCase):
    """
    test coverage for keyring creds accessor
    """
    @mock.patch('cirrus.plugins.creds.keyring.keyring')
    def test_keyring_plugin(self, mock_keyring):
        """test keyring plugin with mocked values for gh creds"""
        mock_instance = mock.Mock()
        mock_instance.get_password = mock.Mock()
        mock_instance.get_password.side_effect = ['steve', 'steves token']
        mock_keyring.get_keyring = mock.Mock()
        mock_keyring.get_keyring.return_value = mock_instance

        plugin = Keyring()

        gh = plugin.github_credentials()
        self.failUnless('github_user' in gh)
        self.failUnless('github_token' in gh)
        self.assertEqual(gh['github_user'], 'steve')
        self.assertEqual(gh['github_token'], 'steves token')

    @mock.patch('cirrus.plugins.creds.keyring.keyring')
    def test_all_methods(self, mock_keyring):
        """test coverage for all methods"""
        mock_instance = mock.Mock()
        mock_instance.get_password = mock.Mock()
        mock_instance.get_password.return_value = 'womp'
        mock_keyring.get_keyring = mock.Mock()
        mock_keyring.get_keyring.return_value = mock_instance
        # test all the methods work with defaults
        plugin = Keyring()
        for n, m in plugin.credential_methods():
            check = m()
            self.failUnless(all(v is 'womp' for v in check.values()))



if __name__ == '__main__':
    unittest.main()
