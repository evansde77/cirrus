'''
tests for git_tools
'''
import mock
import unittest

from cirrus.git_tools import branch
from cirrus.git_tools import checkout_and_pull


class GitToolsTest(unittest.TestCase):

    def test_checkout_and_pull(self):
        with mock.patch('cirrus.git_tools.git') as patch_git:
            mock_repo = mock.Mock()
            patch_git.Repo = mock.Mock()
            patch_git.Repo.return_value = mock_repo
            checkout_and_pull(None, 'master')
            self.failUnless(patch_git.Repo.called)

    def test_branch(self):
        with mock.patch('cirrus.git_tools.git') as patch_git:
            mock_repo = mock.Mock()
            mock_repo.heads = []
            mock_repo.active_branch = 'new_branch'
            patch_git.Repo = mock.Mock()
            patch_git.Repo.return_value = mock_repo
            branch(None, mock_repo.active_branch, 'master')
            self.failUnless(patch_git.Repo.called)


if __name__ == "__main__":
    unittest.main()
