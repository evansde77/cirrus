'''
tests for github_tools
'''
import mock
import unittest

from cirrus.github_tools import build_release_notes
from cirrus.github_tools import create_pull_request
from cirrus.github_tools import format_commit_messages
from cirrus.github_tools import get_commit_msgs
from cirrus.github_tools import get_releases
from cirrus.github_tools import get_tags
from cirrus.github_tools import get_tags_with_sha
from cirrus.github_tools import markdown_format


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

    def tearDown(self):
        """
        teardown mocks
        """
        self.patch_get.stop()

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

    def test_build_release_notes(self):
        """
        _test_build_release_notes_
        """
        tag = {self.release: "123abc"}

        with mock.patch(
            'cirrus.github_tools.get_tags_with_sha') as mock_get_tags_sha:
            with mock.patch(
                'cirrus.github_tools.get_commit_msgs') as mock_get_commit:
                with mock.patch(
                    'cirrus.github_tools.format_commit_messages'
                    ) as mock_format:

                    mock_get_tags_sha.return_value = tag
                    mock_get_commit.return_value = {'sha': 'abc123'}
                    mock_format.return_value = (
                        '- Commit History:'
                        '-- Author: GITHUBUSERNAME'
                        '--- DATETIME: COMMIT MESSAGE'
                        )
                    build_release_notes(self.owner, self.repo, self.release, 'plaintext')
                    self.failUnless(mock_get_tags_sha.called)
                    self.failUnless(mock_get_commit.called)
                    self.failUnless(mock_format.called)

    def test_commit_messages(self):
        """
        _test_commit_messages_

        prints plaintext release notes
        """
        msg = format_commit_messages(self.commit_info)
        print "Plaintext release notes:\n{0}\n".format(msg)

    def test_markdown_format(self):
        """
        _test_markdown_format_

        prints markdown release notes
        """
        msg = markdown_format(self.commit_info)
        print "Markdown release notes:\n{0}\n".format(msg)

    def test_get_commit_msgs(self):
        """
        _test_get_commit_msgs_
        """
        resp_json = [
            {
             'committer': {'login': 'bobing_for_apples'},
             'commit': {
                'message': 'I made a commit',
                'committer': {'date': '2014-08-28'}}
             }
                     ]

        mock_req = mock.Mock()
        mock_req.raise_for_status.return_value = False
        mock_req.json.return_value = resp_json
        self.mock_get.return_value = mock_req

        result = get_commit_msgs(self.owner, self.repo, "abc123", 'token')
        self.failUnless(self.mock_get.called)
        self.failUnless('committer' in result[0])
        self.failUnless('message' in result[0])
        self.failUnless('date' in result[0])

    def test_get_releases(self):
        """
        _test_get_releases_
        """
        resp_json = [
            {
             'tag_name': self.release
             }
                     ]
        mock_req = mock.Mock()
        mock_req.raise_for_status.return_value = False
        mock_req.json.return_value = resp_json
        self.mock_get.return_value = mock_req
        result = get_releases(self.owner, self.repo, 'token')
        self.failUnless(self.mock_get.called)
        self.failUnless('tag_name' in result[0])

    def test_get_tags(self):
        """
        _test_get_tags_
        """
        keys = {'banana': 2, 'apple': 3, 'orange': 1}
        with mock.patch(
            'cirrus.github_tools.get_tags_with_sha') as mock_get_tags_sha:

            mock_get_tags_sha.return_value = keys
            result = get_tags(self.owner, self.repo, 'token')
            self.failUnless(mock_get_tags_sha.called)
            self.failUnlessEqual(result, ['orange', 'banana', 'apple'])

    def test_get_tags_with_sha(self):
        """
        _test_get_tags_with_sha_
        """
        resp_json = [
            {
             'name': self.release,
             'commit': {'sha': 'abc123'}
            }
                     ]
        mock_req = mock.Mock()
        mock_req.raise_for_status.return_value = False
        mock_req.json.return_value = resp_json
        self.mock_get.return_value = mock_req
        result = get_tags_with_sha(self.owner, self.repo, 'token')
        self.failUnless(self.mock_get.called)
        self.failUnlessEqual(
            result,
            {resp_json[0]['name']: resp_json[0]['commit']['sha']})

if __name__ == "__main__":
    unittest.main()
