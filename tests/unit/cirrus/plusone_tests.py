#!/usr/bin/env python
"""
tests for plusone module
"""
import unittest
import mock

from cirrus.plusone import GitHubHelper


class PlusoneTests(unittest.TestCase):

    @mock.patch('cirrus.plusone.requests.Session')
    @mock.patch('cirrus.plusone.get_github_auth')
    def test_plusone(self, mock_gha, mock_sess):
        mock_gha.return_value = ('USER', 'TOKEN')
        mock_session = mock.Mock()
        mock_session.headers = {}
        mock_sess.return_value = mock_session
        GitHubHelper()
        self.assertTrue('Content-Type' in mock_session.headers)
        self.assertTrue('Authorization' in mock_session.headers)
        self.assertEqual(mock_session.headers['Authorization'], 'token TOKEN')

if __name__ == '__main__':
    unittest.main()
