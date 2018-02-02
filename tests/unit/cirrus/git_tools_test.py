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
from cirrus.git_tools import build_release_notes
from cirrus.git_tools import format_commit_messages
from cirrus.git_tools import get_commit_msgs
from cirrus.git_tools import get_tags
from cirrus.git_tools import get_tags_with_sha
from cirrus.git_tools import markdown_format
from cirrus.git_tools import RepoInitializer


class GitToolsTest(unittest.TestCase):

    def setUp(self):
        self.mock_commits = [mock.Mock(), mock.Mock()]
        self.mock_commits[0].committer.name = 'bob'
        self.mock_commits[0].message = 'I made a commit!'
        self.mock_commits[0].committed_date = '1438210783'
        self.mock_commits[1].committer.name = 'tom'
        self.mock_commits[1].message = 'toms commit'
        self.mock_commits[1].committed_date = '1438150783'
        self.mock_tags = [mock.Mock(), mock.Mock(), mock.Mock()]
        self.mock_tags[0].configure_mock(name='banana')
        self.mock_tags[0].commit.committed_date = '1438210002'
        self.mock_tags[0].commit.hexsha = 'BANANA_SHA'
        self.mock_tags[1].configure_mock(name='apple')
        self.mock_tags[1].commit.committed_date = '1438210001'
        self.mock_tags[1].commit.hexsha = 'APPLE_SHA'
        self.mock_tags[2].configure_mock(name='orange')
        self.mock_tags[2].commit.committed_date = '1438210003'
        self.mock_tags[2].commit.hexsha = 'ORANGE_SHA'
        self.mock_repo = mock.Mock()
        self.mock_repo.head.commit.hexsha = 'HEAD_SHA'
        self.mock_repo.iter_commits = mock.Mock()
        self.mock_repo.iter_commits.return_value = self.mock_commits
        self.mock_ret = mock.Mock()
        self.mock_ret.flags = 1
        self.mock_ret.ERROR = 10
        self.mock_repo.remotes.origin.push.side_effect = lambda x: [
            self.mock_ret]
        self.mock_repo.tags = self.mock_tags
        self.patch_git = mock.patch('cirrus.git_tools.git')
        self.mock_git = self.patch_git.start()
        self.mock_git.Repo = mock.Mock()
        self.mock_git.Repo.return_value = self.mock_repo
        self.release = '0.0.0'
        self.commit_info = [
            {
                'committer': 'bob',
                'message': 'I made a commit!',
                'date': '1438210783'},
            {
                'committer': 'tom',
                'message': 'toms commit',
                'date': '1438150783'}
        ]

    def tearDown(self):
        self.patch_git.stop()

    def test_checkout_and_pull(self):
        """
        _test_checkout_and_pull_
        """
        mock_remote = mock.Mock()
        mock_remote.name = 'origin'
        mock_remote.pull = mock.Mock()

        class Remotes(list):
            def __init__(self, m):
                self.append(m)

            def __getattr__(self, name):
                return self[0]

        self.mock_repo.remotes = Remotes(mock_remote)
        self.mock_repo.git = mock.Mock()
        self.mock_repo.git.branch = mock.Mock(
            return_value="develop master remotes/origin/master remotes/origin/develop"
        )
        checkout_and_pull(None, 'master')
        self.failUnless(self.mock_git.Repo.called)
        self.failUnless(mock_remote.pull.called)

    def test_checkout_and_pull_no_remote(self):
        """
        _test_checkout_and_pull_
        """
        mock_remote = mock.Mock()
        mock_remote.name = 'origin'
        mock_remote.pull = mock.Mock()

        class Remotes(list):
            def __init__(self, m):
                self.append(m)

            def __getattr__(self, name):
                return self[0]

        self.mock_repo.remotes = Remotes(mock_remote)
        self.mock_repo.git = mock.Mock()
        self.mock_repo.git.branch = mock.Mock(
            return_value="develop master remotes/origin/develop"
        )
        checkout_and_pull(None, 'master')
        self.failUnless(self.mock_git.Repo.called)
        self.failUnless(not mock_remote.pull.called)

    def test_branch(self):
        """
        _test_branch_
        """
        self.mock_repo.heads = []
        self.mock_repo.active_branch = 'new_branch'
        branch(None, self.mock_repo.active_branch, 'master')
        self.failUnless(self.mock_git.Repo.called)

    def test_push_error(self):
        """
        _test_push_
        """
        mock_ret = mock.Mock()
        mock_ret.flags = 100
        mock_ret.ERROR = 10
        self.mock_repo.remotes.origin.push.side_effect = lambda x: [
            mock_ret]
        self.assertRaises(RuntimeError, push, None)

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

    def test_build_release_notes(self):
        """
        _test_build_release_notes_
        """
        tag = {self.release: "123abc"}

        with mock.patch(
            'cirrus.git_tools.get_tags_with_sha') as mock_get_tags_sha:
            with mock.patch(
                'cirrus.git_tools.get_commit_msgs') as mock_get_commit:

                mock_get_tags_sha.return_value = tag
                mock_get_commit.return_value = self.commit_info
                build_release_notes(
                    None,
                    self.release,
                    'plaintext')
                self.failUnless(mock_get_tags_sha.called)
                self.failUnless(mock_get_commit.called)

    def test_commit_messages(self):
        """
        _test_commit_messages_

        prints plaintext release notes
        """
        msg = format_commit_messages(self.commit_info)
        print("Plaintext release notes:\n{0}\n".format(msg))

    def test_markdown_format(self):
        """
        _test_markdown_format_

        prints markdown release notes
        """
        msg = markdown_format(self.commit_info)
        print("Markdown release notes:\n{0}\n".format(msg))

    def test_get_commit_msgs(self):
        """
        _test_get_commit_msgs_
        """
        result = get_commit_msgs(None, 'RANDOM_SHA')
        self.failUnless('committer' in result[0])
        self.failUnless('message' in result[0])
        self.failUnless('date' in result[0])
        self.failUnless('committer' in result[1])
        self.failUnless('message' in result[1])
        self.failUnless('date' in result[1])

    def test_get_tags(self):
        """
        _test_get_tags_
        """
        result = get_tags(None)
        self.failUnlessEqual(result, ['orange', 'banana', 'apple'])

    def test_get_tags_with_sha(self):
        """
        _test_get_tags_with_sha_
        """
        result = get_tags_with_sha(None)
        self.assertEqual(result['orange'], 'ORANGE_SHA')
        self.assertEqual(result['apple'], 'APPLE_SHA')
        self.assertEqual(result['banana'], 'BANANA_SHA')


class RepoInitializerTest(unittest.TestCase):
    """tests for RepoInitializer"""
    def setUp(self):
        self.patch_git = mock.patch('cirrus.git_tools.git')
        self.mock_git = self.patch_git.start()
        self.mock_repo = mock.Mock()
        self.mock_repo.head = "HEAD"
        self.mock_repo.create_head = mock.Mock()
        self.mock_repo.git = mock.Mock()
        self.mock_repo.git.commit = mock.Mock()

        class Heads(list):
            def __init__(self, *m):
                self.extend(list(m))

            def __getattr__(self, name):
                for x in self:
                    if x.name == name:
                        return x

            def __getitem__(self, name):
                for x in self:
                    if x.name == name:
                        return x


        mock_result = mock.Mock()
        mock_result.flags = 1
        mock_result.ERROR = 10

        self.mock_remote = mock.Mock()
        self.mock_remote.name = 'origin'
        self.mock_remote.fetch = mock.Mock()
        self.mock_remote.refs = {'develop': mock.Mock(name="develop_ref"),'master': mock.Mock(name="master_ref")}
        self.mock_remote.push = mock.Mock(return_value=[mock_result])

        mock_head1 = mock.Mock()
        mock_head1.name = 'master'
        mock_head1.commit = "COMMIT1"
        mock_head2 = mock.Mock()
        mock_head2.name = 'develop'
        mock_head1.commit = "COMMIT2"
        mock_head1.tracking_branch = mock.Mock(return_value=None)
        mock_head2.tracking_branch = mock.Mock(return_value=None)

        self.mock_repo.remotes = Heads(self.mock_remote)
        self.mock_repo.heads = Heads(mock_head1, mock_head2)
        self.mock_git.Repo = mock.Mock()
        self.mock_git.Repo.return_value = self.mock_repo

    def tearDown(self):
        self.patch_git.stop()

    def test_repo_init(self):
        repo_init = RepoInitializer()
        repo_init.branch_exists_origin = mock.Mock(return_value=False)
        repo_init.init_branch('master', 'origin', True)
        repo_init.init_branch('develop', 'origin', True)

        self.assertTrue(self.mock_repo.git.commit.called)
        self.assertTrue(self.mock_repo.create_head.called)
        self.assertTrue(self.mock_remote.push.called)
        self.assertTrue(self.mock_remote.fetch.called)
        self.mock_remote.push.assert_has_calls([
            mock.call('master'),
            mock.call('develop')
        ])

        self.mock_repo.create_head.assert_has_calls([
            mock.call('master', 'HEAD'),
            mock.call('develop', 'HEAD')
        ])


if __name__ == "__main__":
    unittest.main()
