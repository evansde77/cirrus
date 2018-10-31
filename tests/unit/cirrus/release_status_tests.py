#!/usr/bin/env python
"""
tests for release status module
"""

import unittest
import mock

from cirrus.release_status import release_status


class ReleaseStatusTests(unittest.TestCase):
    """
    test case for release status
    """

    def setUp(self):
        self.patch_ghc = mock.patch('cirrus.release_status.GitHubContext')
        self.mock_ghc = mock.Mock()
        self.mock_ghc_ctor = self.patch_ghc.start()
        mock_ghc_ctx = mock.Mock()
        mock_ghc_ctx.__enter__ = mock.Mock(return_value=self.mock_ghc)
        mock_ghc_ctx.__exit__ = mock.Mock()
        self.mock_ghc_ctor.return_value = mock_ghc_ctx
        self.mock_conf = mock.Mock()
        self.mock_conf.gitflow_release_prefix = mock.Mock(return_value='release/')
        self.mock_conf.gitflow_branch_name = mock.Mock(return_value='develop')
        self.mock_conf.gitflow_master_name = mock.Mock(return_value='master')
        self.mock_conf.gitflow_origin_name = mock.Mock(return_value='origin')
        self.mock_ghc.config = self.mock_conf

        self.mock_ghc.find_release_commit = mock.Mock(side_effect=["BRANCH_COMMIT", "TAG_COMMIT"])
        self.mock_ghc.commit_on_branches = mock.Mock(return_value=['master', 'remotes/origin/master'])
        self.mock_ghc.merge_base = mock.Mock(return_value="MERGE_COMMIT")
        self.mock_ghc.git_show_commit = mock.Mock(return_value=" this contains release/0.2.3 blah")
        self.mock_ghc.unmerged_releases = mock.Mock(return_value=['release/UNMERGED'])

    def tearDown(self):
        self.patch_ghc.stop()

    def test_release_status_on_develop(self):
        """test succesful release status with tag name"""
        self.assertTrue(not release_status('develop'))
        self.mock_ghc.unmerged_releases.assert_called()

    def test_release_status(self):
        """test succesful release status with tag name"""
        self.assertTrue(release_status('release/0.2.3'))

    def test_release_status_branch(self):
        """test successful release status with branch name"""
        self.assertTrue(release_status('release/0.2.3'))

    def test_bad_release_tag(self):
        """verify bad tag/release branch"""
        self.mock_ghc.find_release_commit.side_effect = [None, None]
        self.assertTrue(not release_status('release/0.2.3'))

    def test_missing_merges(self):
        self.mock_ghc.merge_base.return_value = None
        self.assertTrue(not release_status('0.2.3'))


if __name__ == '__main__':
    unittest.main()
