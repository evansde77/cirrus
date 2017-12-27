'''
tests for github_tools
'''
import os
import json
import mock
import unittest
import subprocess

from cirrus.github_tools import create_pull_request
from cirrus.github_tools import current_branch_mark_status
from cirrus.github_tools import get_releases
from cirrus.github_tools import GitHubContext
from git.exc import GitCommandError
from .harnesses import _repo_directory

class GithubToolsTest(unittest.TestCase):
    """
    _GithubToolsTest_
    """
    def setUp(self):
        """
        setup mocks
        """
        self.owner = 'testorg'
        self.repo = 'testrepo'
        self.release = '0.0.0'
        self.commit_info = [
            {
                'committer': 'bob',
                'message': 'I made a commit!',
                'date': '2014-08-28'},
            {
                'committer': 'tom',
                'message': 'toms commit',
                'date': '2014-08-27'}]

        self.patch_get = mock.patch('cirrus.github_tools.requests.get')
        self.mock_get = self.patch_get.start()
        self.patch_environ = mock.patch.dict(os.environ,
            {
                'HOME': 'unittest',
                'USER': 'steve'
            }
        )
        self.patch_environ.start()
        self.gitconf_str = "cirrus.credential-plugin=default"
        self.patch_gitconfig = mock.patch('cirrus.gitconfig.shell_command')
        self.mock_gitconfig = self.patch_gitconfig.start()
        self.mock_gitconfig.return_value = self.gitconf_str

    def tearDown(self):
        """
        teardown mocks
        """
        self.patch_environ.stop()
        self.patch_get.stop()
        self.patch_gitconfig.stop()

    def test_create_pull_request(self):
        """
        _test_create_pull_request_
        """
        resp_json = {'html_url': 'https://github.com/{0}/{1}/pull/1'.format(self.owner, self.repo)}
        with mock.patch(
            'cirrus.github_tools.load_configuration') as mock_config_load:

            mock_config_load.organisation_name.return_value = self.owner
            mock_config_load.package_name.return_value = self.repo
            with mock.patch(
                'cirrus.github_tools.get_active_branch') as mock_get_branch:

                with mock.patch(
                    'cirrus.github_tools.requests.post') as mock_post:
                    mock_resp = mock.Mock()
                    mock_resp.raise_for_status.return_value = False
                    mock_resp.json.return_value = resp_json
                    mock_post.return_value = mock_resp

                    with mock.patch(
                        'cirrus.github_tools.json.dumps') as mock_dumps:
                        result = create_pull_request(
                            self.repo,
                            {'title': 'Test', 'body': 'This is a test'},
                            'token')
                        self.failUnless(mock_config_load.called)
                        self.failUnless(mock_get_branch.called)
                        self.failUnless(mock_post.called)
                        self.failUnless(mock_dumps.called)
                        self.failUnlessEqual(result, resp_json['html_url'])

    def test_get_releases(self):
        """
        _test_get_releases_
        """
        resp_json = [
            {'tag_name': self.release}
        ]
        mock_req = mock.Mock()
        mock_req.raise_for_status.return_value = False
        mock_req.json.return_value = resp_json
        self.mock_get.return_value = mock_req
        result = get_releases(self.owner, self.repo, 'token')
        self.failUnless(self.mock_get.called)
        self.failUnless('tag_name' in result[0])

    @mock.patch('cirrus.github_tools.load_configuration')
    @mock.patch("cirrus.github_tools.requests.post")
    @mock.patch("cirrus.github_tools.push")
    def test_current_branch_mark_status(self, mock_push, mock_post, mock_config_load):
        """
        _test_current_branch_mark_status_

        """
        def check_post(url, headers, data):
            self.assertTrue(url.startswith("https://api.github.com/repos/"))
            data = json.loads(data)
            self.assertEqual(data.get("state"), "success")
            self.assertTrue(data.get("description"))
            self.assertTrue(data.get("context"))
            return mock.Mock()

        mock_post.side_effect = check_post

        mock_config_load.organisation_name.return_value = self.owner
        mock_config_load.package_name.return_value = self.repo

        current_branch_mark_status(_repo_directory(), "success")

        self.failUnless(mock_post.called)

    @mock.patch('cirrus.github_tools.git')
    def test_push_branch(self, mock_git):
        mock_repo = mock.Mock()
        mock_repo.active_branch = mock.Mock()
        mock_repo.active_branch.name = 'womp'
        mock_repo.head = "HEAD"
        mock_repo.git = mock.Mock()
        mock_repo.git.checkout = mock.Mock()
        mock_git.Repo = mock.Mock(return_value=mock_repo)
        mock_repo.remotes = mock.Mock()
        mock_ret = mock.Mock()
        mock_ret.flags = 1000
        mock_ret.ERROR = 10000
        mock_ret.summary = "SUMMARY"
        mock_repo.remotes.origin = mock.Mock()
        mock_repo.remotes.origin.push = mock.Mock(return_value=[mock_ret])
        ghc = GitHubContext('REPO')

        ghc.push_branch('womp')
        self.failUnless(mock_repo.remotes.origin.push.called)
        mock_repo.remotes.origin.push.assert_has_calls([mock.call('HEAD')])

        mock_repo.remotes.origin.push = mock.Mock(side_effect=GitCommandError('A', 128))
        self.assertRaises(RuntimeError, ghc.push_branch, 'womp2')

    @mock.patch('cirrus.github_tools.git')
    @mock.patch('cirrus.github_tools.time.sleep')
    def test_push_branch_with_retry(self, mock_sleep, mock_git):
        mock_repo = mock.Mock()
        mock_repo.active_branch = mock.Mock()
        mock_repo.active_branch.name = 'womp'
        mock_repo.git = mock.Mock()
        mock_repo.git.checkout = mock.Mock()
        mock_git.Repo = mock.Mock(return_value=mock_repo)
        mock_ret_f = mock.Mock()
        mock_ret_f.flags = 1
        mock_ret_f.ERROR = 0
        mock_ret_f.summary = "mock failure summary"
        mock_ret_ok = mock.Mock()
        mock_ret_ok.flags = 0
        mock_ret_ok.ERROR = 1
        mock_repo.remotes = mock.Mock()
        mock_repo.remotes.origin = mock.Mock()
        mock_repo.remotes.origin.push = mock.Mock(
            side_effect=[[mock_ret_f], [mock_ret_f], [mock_ret_ok]]
        )

        ghc = GitHubContext('REPO')

        ghc.push_branch_with_retry('womp', attempts=3, cooloff=2)
        self.assertEqual(mock_repo.remotes.origin.push.call_count, 3)

        mock_repo.remotes.origin.push = mock.Mock(side_effect=GitCommandError('B', 128))
        self.assertRaises(RuntimeError, ghc.push_branch_with_retry, 'womp', attempts=3, cooloff=2)

    @mock.patch('cirrus.github_tools.git')
    def test_tag_release(self, mock_git):
        """test tag_release call"""
        mock_repo = mock.Mock()
        mock_repo.active_branch = mock.Mock()
        mock_repo.active_branch.name = 'master'
        mock_repo.git = mock.Mock()
        mock_repo.git.checkout = mock.Mock()
        mock_tag1 = mock.Mock()
        mock_tag1.name = '0.0.0'
        mock_tag2 = mock.Mock()
        mock_tag2.name = '0.0.1'
        mock_repo.tags = [
            mock_tag1, mock_tag2
        ]
        mock_repo.create_tag = mock.Mock()
        mock_git.Repo = mock.Mock(return_value=mock_repo)
        mock_repo.remotes = mock.Mock()
        mock_repo.remotes.origin = mock.Mock()
        mock_repo.remotes.origin.push = mock.Mock()

        ghc = GitHubContext('REPO')
        ghc.tag_release('0.0.2', 'master', push=True, attempts=2, cooloff=0)

        self.failUnless(mock_repo.create_tag.called)
        self.failUnless(mock_repo.remotes.origin.push.called)

    @mock.patch('cirrus.github_tools.git')
    @mock.patch('cirrus.github_tools.time')
    def test_tag_release_retry(self, mock_time, mock_git):
        """test repeated tries to push tags"""
        mock_repo = mock.Mock()
        mock_repo.active_branch = mock.Mock()
        mock_repo.active_branch.name = 'master'
        mock_repo.git = mock.Mock()
        mock_repo.git.checkout = mock.Mock()
        mock_tag1 = mock.Mock()
        mock_tag1.name = '0.0.0'
        mock_tag2 = mock.Mock()
        mock_tag2.name = '0.0.1'
        mock_repo.tags = [
            mock_tag1, mock_tag2
        ]
        mock_repo.create_tag = mock.Mock()
        mock_git.Repo = mock.Mock(return_value=mock_repo)
        mock_repo.remotes = mock.Mock()
        mock_repo.remotes.origin = mock.Mock()
        mock_repo.remotes.origin.push = mock.Mock(
            side_effect=RuntimeError("push it real good")
        )
        mock_time.sleep = mock.Mock()

        ghc = GitHubContext('REPO')
        self.assertRaises(
            RuntimeError,
            ghc.tag_release,
            '0.0.2',
            'master',
            push=True,
            attempts=5,
            cooloff=0
        )
        self.assertEqual(mock_repo.remotes.origin.push.call_count, 5)
        self.assertEqual(mock_time.sleep.call_count, 5)
        self.failUnless(mock_repo.create_tag.called)

    @mock.patch('cirrus.github_tools.git')
    def test_merge_branch(self, mock_git):
        """test merge branch"""
        mock_repo = mock.Mock()
        mock_repo.git = mock.Mock()
        mock_repo.git.merge = mock.Mock()
        mock_git.Repo = mock.Mock(return_value=mock_repo)
        ghc = GitHubContext('REPO')
        ghc.merge_branch('develop')
        self.assertTrue(mock_repo.git.merge.called)

    @mock.patch('cirrus.github_tools.git')
    def test_merge_branch_conflict(self, mock_git):
        """test merge branch"""
        mock_repo = mock.Mock()
        mock_repo.git = mock.Mock()
        mock_repo.git.merge = mock.Mock(side_effect=GitCommandError(["git", "command"], "stdout", "stderr"))
        mock_repo.active_branch = mock.Mock()
        mock_repo.active_branch.name = "ACTIVE"
        mock_repo.index = mock.Mock()
        mock_repo.index.unmerged_blobs = mock.Mock(
            return_value={'file1': [(1, "BLOB1")], 'file2': [(2, "BLOB2")]}
        )
        mock_git.Repo = mock.Mock(return_value=mock_repo)
        ghc = GitHubContext('REPO')
        self.assertRaises(GitCommandError, ghc.merge_branch, 'develop')



if __name__ == "__main__":
    unittest.main()
