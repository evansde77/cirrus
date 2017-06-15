#!/usr/bin/env python
"""
scp tests
"""


import unittest
import mock
from cirrus.scp import SCP, put

class ScpTests(unittest.TestCase):

    @mock.patch('cirrus.scp.local')
    def test_scp(self, mock_local):
        s = SCP(
            target_host="HOST",
            target_path="/PATH",
            source="somefile",
            ssh_username="steve",
            ssh_keyfile="steves_key",
            ssh_config="~/.ssh/config"
        )
        comm = s.scp_command
        self.assertTrue('somefile' in comm)
        self.assertTrue('steve@HOST:/PATH' in comm)
        self.assertTrue('-i steves_key' in comm)

        s()
        mock_local.assert_has_calls(mock.call(s.scp_command))


if __name__ =='__main__':
    unittest.main()

