#!/usr/bin/env python
"""
invoke_helper_tests

"""

import unittest
import mock
import invoke
from cirrus.invoke_helpers import local



class InvokeHelperTests(unittest.TestCase):

    @mock.patch('cirrus.invoke_helpers.Context')
    def test_local_ok(self, mock_invoke):
        mock_ctx = mock.Mock()
        mock_ctx.run = mock.Mock()
        mock_invoke.return_value=mock_ctx

        comm = "/bin/ls"

        local(comm)
        self.assertTrue(mock_ctx.run.called)

    @mock.patch('cirrus.invoke_helpers.Context')
    def test_local_fail(self, mock_invoke):
        mock_ctx = mock.Mock()
        mock_ctx.run = mock.Mock()
        mock_ctx.run.side_effect = invoke.exceptions.UnexpectedExit(
            invoke.Result(
                command="command",
                shell="shell",
                stdout="stdout",
                stderr="stderr",
                exited=10,
                pty=False
            )
        )
        mock_invoke.return_value = mock_ctx
        comm = "/bin/ls"
        self.assertRaises(invoke.exceptions.UnexpectedExit, local, comm)



if __name__ == '__main__':
    unittest.main()
