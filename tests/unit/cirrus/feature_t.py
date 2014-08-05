"""
feature command tests

"""
import mock
import os
import tempfile
import unittest

from cirrus.feature import new_feature_branch
from cirrus.feature import push_feature

from harnesses import CirrusConfigurationHarness, write_cirrus_conf


class FeatureCommandTest(unittest.TestCase):
    """
    Test Case for new_feature_branch function
    """
    def setUp(self):
        """set up test files"""
        self.dir = tempfile.mkdtemp()
        self.config = os.path.join(self.dir, 'cirrus.conf')
        write_cirrus_conf(self.config,
            {'name': 'cirrus_unittest', 'version': '1.2.3'},
            {'develop_branch': 'develop', 'feature_branch_prefix': 'feature/'}
            )
        self.harness = CirrusConfigurationHarness(
            'cirrus.feature.load_configuration',
            self.config)
        self.harness.setUp()
        self.patch_pull = mock.patch('cirrus.feature.checkout_and_pull')
        self.patch_branch = mock.patch('cirrus.feature.branch')
        self.mock_pull = self.patch_pull.start()
        self.mock_branch = self.patch_branch.start()

    def tearDown(self):
        self.patch_pull.stop()
        self.patch_branch.stop()
        self.harness.tearDown()
        if os.path.exists(self.dir):
            os.system('rm -rf {0}'.format(self.dir))

    def test_new_feature_branch(self):
        """
        _test_new_feature_branch_
        """
        opts = mock.Mock()
        opts.command = 'new'
        opts.name = 'testbranch'

        new_feature_branch(opts)
        self.failUnless(self.mock_pull.called)
        self.assertEqual(self.mock_pull.call_args[0][1], 'develop')
        self.failUnless(self.mock_branch.called)
        self.assertEqual(
            self.mock_branch.call_args[0][1],
            ''.join(('feature/', opts.name)))

    def test_push_feature(self):
        """
        _test_push_feature_
        """
        opts = mock.Mock()
        opts.command = 'push'
        opts.c_msg = 'test message'
        opts.c_files = 'file1.txt,file2.py,file3.py'

        with mock.patch('cirrus.feature.commit_files') as mock_commit:
            push_feature(opts)
            self.failUnless(mock_commit.called)
            self.failUnlessAlmostEqual(
                mock_commit.call_args[0][1],
                opts.c_msg,
                opts.c_files.split(','))

if __name__ == '__main__':
    unittest.main()
