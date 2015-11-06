'''
tests for github_tools
'''
import json
import mock
import unittest

from cirrus.github_tools import create_pull_request
from cirrus.github_tools import current_branch_mark_status
from cirrus.github_tools import get_releases


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

    @mock.patch('cirrus.github_tools.load_configuration')
    @mock.patch("cirrus.github_tools.requests.post")
    def test_current_branch_mark_status(self, mock_post, mock_config_load):
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

        current_branch_mark_status(".", "success")

        self.failUnless(mock_post.called)

if __name__ == "__main__":
    unittest.main()
