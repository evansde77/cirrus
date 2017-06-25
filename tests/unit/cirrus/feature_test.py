"""
feature command tests

"""
import mock
import os
import tempfile
import unittest

from cirrus.feature import new_feature_branch, new_pr

from .harnesses import CirrusConfigurationHarness, write_cirrus_conf


class FeatureCommandTest(unittest.TestCase):
    """
    Test Case for new_feature_branch function
    """
    def setUp(self):
        """set up test files"""
        self.dir = tempfile.mkdtemp()
        self.config = os.path.join(self.dir, 'cirrus.conf')
        write_cirrus_conf(self.config, **{
            'package': {
                'name': 'cirrus_unittest',
                'version': '1.2.3',
                'organization': 'testorg',
                'owner': 'Bob'},
            'gitflow': {
                'develop_branch': 'develop',
                'feature_branch_prefix': 'feature/'}})
        self.harness = CirrusConfigurationHarness(
            'cirrus.feature.load_configuration',
            self.config)
        self.harness.setUp()
        self.patch_pull = mock.patch('cirrus.feature.checkout_and_pull')
        self.patch_branch = mock.patch('cirrus.feature.branch')
        self.patch_push = mock.patch('cirrus.feature.push')
        self.mock_pull = self.patch_pull.start()
        self.mock_branch = self.patch_branch.start()
        self.mock_push = self.patch_push.start()

    def tearDown(self):
        self.harness.tearDown()
        self.patch_pull.stop()
        self.patch_branch.stop()
        self.patch_push.stop()
        if os.path.exists(self.dir):
            os.system('rm -rf {0}'.format(self.dir))

    def test_new_feature_branch(self):
        """
        _test_new_feature_branch_
        """
        opts = mock.Mock()
        opts.command = 'new'
        opts.name = 'testbranch'
        opts.push = False
        opts.no_remote = True

        new_feature_branch(opts)
        self.failUnless(self.mock_pull.called)
        self.assertEqual(self.mock_pull.call_args[0][1], 'develop')
        self.failUnless(self.mock_branch.called)
        self.failIf(self.mock_push.called)

    def test_new_feature_branch_push(self):
        """
        _test_new_feature_branch_push_

        test creating a new feature branch and pushing it to
        remote
        """
        opts = mock.Mock()
        opts.command = 'new'
        opts.name = 'testbranch'
        opts.push = True
        opts.no_remote = False

        new_feature_branch(opts)
        self.failUnless(self.mock_pull.called)
        self.assertEqual(self.mock_pull.call_args[0][1], 'develop')
        self.failUnless(self.mock_branch.called)
        self.failUnless(self.mock_push.called)

    def test_new_pr(self):
        """
        _test_new_pr_
        """
        opts = mock.Mock()
        opts.command = 'pull-request'
        opts.title = 'Fancy Title Here'
        opts.body = 'Super descriptive description.'
        opts.notify = '@nobody'

        with mock.patch('cirrus.feature.create_pull_request') as mock_pr:
            new_pr(opts)
            self.failUnless('body' in mock_pr.call_args[0][1])
            self.failUnless('title' in mock_pr.call_args[0][1])
            self.failUnless(mock_pr.called)


if __name__ == '__main__':
    unittest.main()
