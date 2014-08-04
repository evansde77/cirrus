'''
tests for git_tools
'''
import mock
import unittest

from cirrus.git_tools import checkout_and_pull
# from tests.test_harness import GitTestHarness


class GitToolsTest(unittest.TestCase):

    def setUp(self):
        self.repo_url = 'test/repo'
        self.patch_git = mock.patch('cirrus.git_tools.git')
        self.patch_git.start()
        self.mock_repo = mock.Mock()
        self.mock_repo.git_dir = self.repo_url
        self.mock_repo.heads.master = mock.Mock()

        self.patch_git.Repo = mock.Mock()
        self.patch_git.Repo.return_value = self.mock_repo

    def tearDown(self):
        self.patch_git.stop()

    def test_checkout_and_pull(self):
        with mock.patch('cirrus.git_tools.checkout_and_pull') as mock_pull:
            checkout_and_pull(self.repo_url, 'master')
            self.failUnless(mock_pull.called)


if __name__ == "__main__":
    unittest.main()
