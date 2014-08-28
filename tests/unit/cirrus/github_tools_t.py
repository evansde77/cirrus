'''
tests for github_tools
'''
import mock
import unittest

from cirrus.github_tools import build_release_notes
from cirrus.github_tools import create_pull_request

OWNER = 'testorg'
REPO = 'testrepo'
RELEASE = '0.0.0'


class GithubToolsTest(unittest.TestCase):
    """
    _GithubToolsTest_
    """

    def test_create_pull_request(self):
        """
        _test_create_pull_request_
        """
        resp_json = {'html_url': 'https://github.com/{0}/{1}/pull/1'.format(OWNER, REPO)}
        with mock.patch(
            'cirrus.github_tools.load_configuration') as mock_config_load:

            mock_config_load.organisation_name.return_value = OWNER
            mock_config_load.package_name.return_value = REPO
            with mock.patch(
                'cirrus.github_tools.get_active_branch') as mock_get_branch:

                with mock.patch(
                    'cirrus.github_tools.requests.post') as mock_post:

                    with mock.patch(
                        'cirrus.github_tools.json.dumps') as mock_dumps:

                        mock_post.raise_for_status.return_value = False
                        mock_post.resp.json.return_value = resp_json
                        create_pull_request(
                            REPO,
                            {'title': 'Test', 'body': 'This is a test'},
                            'token')
                        self.failUnless(mock_config_load.called)
                        self.failUnless(mock_get_branch.called)
                        self.failUnless(mock_post.called)
                        self.failUnless(mock_dumps.called)

    def test_build_release_notes(self):
        """
        _test_build_release_notes_
        """
        tag = {RELEASE: "123abc"}

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
                    build_release_notes(OWNER, REPO, RELEASE)
                    self.failUnless(mock_get_tags_sha.called)
                    self.failUnless(mock_get_commit.called)
                    self.failUnless(mock_format.called)

if __name__ == "__main__":
    unittest.main()
