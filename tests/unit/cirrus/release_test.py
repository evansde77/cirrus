#!/usr/bin/env python
"""
release command tests

"""
import os
import unittest
import tempfile
import mock

from cirrus.release import new_release
from cirrus.release import upload_release
from cirrus.release import build_release
from cirrus.configuration import Configuration

from harnesses import CirrusConfigurationHarness, write_cirrus_conf

class ReleaseNewCommandTest(unittest.TestCase):
    """
    Test Case for new_release function
    """
    def setUp(self):
        """set up test files"""
        self.dir = tempfile.mkdtemp()
        self.config = os.path.join(self.dir, 'cirrus.conf')
        write_cirrus_conf(self.config,
            **{
                'package': {'name': 'cirrus_unittest', 'version': '1.2.3'},
                'gitflow': {'develop_branch': 'develop', 'release_branch_prefix': 'release/'},
                }
            )
        self.harness = CirrusConfigurationHarness('cirrus.release.load_configuration', self.config)
        self.harness.setUp()
        self.patch_pull = mock.patch('cirrus.release.checkout_and_pull')
        self.patch_branch = mock.patch('cirrus.release.branch')
        self.patch_commit = mock.patch('cirrus.release.commit_files')
        self.mock_pull = self.patch_pull.start()
        self.mock_branch = self.patch_branch.start()
        self.mock_commit = self.patch_commit.start()

    def tearDown(self):
        self.patch_pull.stop()
        self.patch_branch.stop()
        self.patch_commit.stop()
        self.harness.tearDown()
        if os.path.exists(self.dir):
            os.system('rm -rf {0}'.format(self.dir))


    def test_new_release(self):
        """
        _test_new_release_

        """
        opts = mock.Mock()
        opts.micro = True
        opts.major = False
        opts.minor = False
        opts.bump = None

        # should create a new minor release, editing
        # the cirrus config in the test dir
        new_release(opts)

        # verify new version
        new_conf = Configuration(self.config)
        new_conf.load()
        self.assertEqual(new_conf.package_version(), '1.2.4')

        self.failUnless(self.mock_pull.called)
        self.assertEqual(self.mock_pull.call_args[0][1], 'develop')
        self.failUnless(self.mock_branch.called)
        self.assertEqual(self.mock_branch.call_args[0][1], 'release/1.2.4')
        self.failUnless(self.mock_commit.called)
        self.assertEqual(self.mock_commit.call_args[0][2], 'cirrus.conf')


class ReleaseBuildCommandTest(unittest.TestCase):
    """
    test case for cirrus release build command

    """
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.config = os.path.join(self.dir, 'cirrus.conf')
        write_cirrus_conf(self.config,
            **{
                'package': {'name': 'cirrus_unittest', 'version': '1.2.3'},
                'gitflow': {'develop_branch': 'develop', 'release_branch_prefix': 'release/'}
            }
            )
        self.harness = CirrusConfigurationHarness('cirrus.release.load_configuration', self.config)
        self.harness.setUp()

        self.patch_local =  mock.patch('cirrus.release.local')
        self.mock_local = self.patch_local.start()

    def tearDown(self):
        self.harness.tearDown()
        self.patch_local.stop()

    def test_build_command_raises(self):
        """should raise when build artifact is not present"""
        opts = mock.Mock()
        self.assertRaises(RuntimeError, build_release, opts)

    def test_build_command(self):
        """test calling build, needs os.path.exists mocks since we arent actually building"""
        with mock.patch('cirrus.release.os') as mock_os:

            mock_os.path = mock.Mock()
            mock_os.path.exists = mock.Mock()
            mock_os.path.exists.return_value = True
            mock_os.path.join = mock.Mock()
            mock_os.path.join.return_value = 'build_artifact'

            opts = mock.Mock()
            result = build_release(opts)
            self.assertEqual(result, 'build_artifact')
            self.failUnless(mock_os.path.exists.called)
            self.assertEqual(mock_os.path.exists.call_args[0][0], 'build_artifact')

            self.failUnless(self.mock_local.called)
            self.assertEqual(self.mock_local.call_args[0][0], 'python setup.py sdist')


@unittest.skip("fix this to test with plugins")
class ReleaseUploadCommandTest(unittest.TestCase):
    """
    test case for cirrus release upload command
    """
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.config = os.path.join(self.dir, 'cirrus.conf')
        write_cirrus_conf(self.config,
            **{
                'package' :{'name': 'cirrus_unittest', 'version': '1.2.3'},
                'github': {'develop_branch': 'develop', 'release_branch_prefix': 'release/'},
                'pypi': {
                    'pypi_upload_path': '/opt/pypi',
                    'pypi_url': 'pypi.cloudant.com',
                    'pypi_username': 'steve',
                    'pypi_ssh_key': 'steves_creds'
                }
            }
            )
        self.harness = CirrusConfigurationHarness('cirrus.release.load_configuration', self.config)
        self.harness.setUp()

        self.patch_put =  mock.patch('cirrus.release.put')
        self.mock_put = self.patch_put.start()


    def tearDown(self):
        self.harness.tearDown()
        self.patch_put.stop()


    @mock.patch('cirrus.release.current_branch_mark_status')
    @mock.patch('cirrus.release.wait_on_gh_status')
    @mock.patch('cirrus.release.get_active_branch')
    @mock.patch('cirrus.release.checkout_and_pull')
    @mock.patch('cirrus.release.merge')
    @mock.patch('cirrus.release.push')
    @mock.patch('cirrus.release.tag_release')
    def test_release_upload(self, m_tag_release, m_push, m_merge, m_checkout_and_pull, m_get_active_branch, m_wait_on_gh_status, m_current_branch_mark_status):
        """test upload command, mocking out fabric put"""
        mock_branch = mock.Mock()
        mock_branch.name = "release/1.2.3"
        m_get_active_branch.return_value = mock_branch

        with mock.patch('cirrus.release.os') as mock_os:
            mock_os.path = mock.Mock()
            mock_os.path.exists = mock.Mock()
            mock_os.path.exists.return_value = True
            mock_os.path.join = mock.Mock()
            mock_os.path.join.return_value = 'build_artifact'

            opts = mock.Mock()
            opts.no_upload = False
            opts.test = False
            upload_release(opts)

            self.failUnless(mock_os.path.exists.called)
            self.failUnless(self.mock_put.called)
            self.assertEqual(self.mock_put.call_args[0][0], 'build_artifact')
            self.assertEqual(self.mock_put.call_args[0][1], '/opt/pypi' )
            self.assertEqual(mock_os.path.exists.call_args[0][0], 'build_artifact')

            self.assertEqual(m_tag_release.call_args[0][1], '1.2.3')
            self.assertEqual(m_tag_release.call_args[0][2], 'master')
            self.failUnless(m_merge.called)
            self.failUnless(m_push.called)
            self.assertEqual(m_push.call_count, 2)
            self.failUnless(m_checkout_and_pull.called)

            self.failUnless(m_current_branch_mark_status.called)


if __name__ == '__main__':
    unittest.main()
