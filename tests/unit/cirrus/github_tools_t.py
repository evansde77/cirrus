'''
tests for github_tools
'''
import mock
import unittest

from cirrus.github_tools import build_release_notes

OWNER = 'testorg'
REPO = 'testrepo'
RELEASE = '0.0.0'


class GithubToolsTest(unittest.TestCase):

    def test_build_release_notes(self):
        """
        _test_build_release_notes_
        """
        tag = {
            'name': RELEASE,
            'zipball_url': "https://api.github.com/repos/{0}/{1}/zipball/{2}".format(OWNER, REPO, RELEASE),
            'tarball_url': "https://api.github.com/repos/{0}/{1}/tarball/{2}".format(OWNER, REPO, RELEASE),
            'commit': {
                'sha': "123abc",
                'url': "https://api.github.com/repos/{0}/{1}/commits/abc123".format(OWNER, REPO)
                }
            }

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
