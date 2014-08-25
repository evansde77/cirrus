'''
tests for git_tools
'''
import mock
import unittest

from cirrus.git_tools import branch
from cirrus.git_tools import checkout_and_pull
from cirrus.git_tools import get_active_branch
from cirrus.git_tools import get_diff_files
from cirrus.git_tools import merge
from cirrus.git_tools import push


class GitToolsTest(unittest.TestCase):

    def setUp(self):
        self.mock_repo = mock.Mock()
        self.patch_git = mock.patch('cirrus.git_tools.git')
        self.mock_git = self.patch_git.start()
        self.mock_git.Repo = mock.Mock()
        self.mock_git.Repo.return_value = self.mock_repo

    def tearDown(self):
        self.patch_git.stop()

    def test_checkout_and_pull(self):
        """
        _test_checkout_and_pull_
        """
        checkout_and_pull(None, 'master')
        self.failUnless(self.mock_git.Repo.called)

    def test_branch(self):
        """
        _test_branch_
        """
        self.mock_repo.heads = []
        self.mock_repo.active_branch = 'new_branch'
        branch(None, self.mock_repo.active_branch, 'master')
        self.failUnless(self.mock_git.Repo.called)

    def test_push(self):
        """
        _test_push_
        """
        push(None)
        self.failUnless(self.mock_git.Repo.called)

    def test_get_active_branch(self):
        """
        _test_get_active_branch_
        """
        get_active_branch(None)
        self.failUnless(self.mock_git.Repo.called)

    def test_merge(self):
        branch1 = 'branch1'
        branch2 = 'branch2'

        merge(None, branch1, branch2)
        self.failUnless(self.mock_git.Repo.called)

    def test_get_diff_files(self):
        path = "path/to/file/hello.py"
        self.mock_blob = mock.Mock()
        self.mock_blob.a_blob.path = path
        self.mock_repo.index.diff.return_value = [self.mock_blob]

        diffs = get_diff_files(None)
        self.failUnlessEqual(diffs[0], path)
        self.failUnless(self.mock_git.Repo.called)

if __name__ == "__main__":
    unittest.main()
