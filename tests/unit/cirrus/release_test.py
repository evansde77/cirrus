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
from cirrus.release import cleanup_release
from cirrus.release import artifact_name
from cirrus.configuration import Configuration
from cirrus._2to3 import to_str
from pluggage.errors import FactoryError

from .harnesses import CirrusConfigurationHarness, write_cirrus_conf


class ReleaseNewCommandTest(unittest.TestCase):
    """
    Test Case for new_release function
    """
    def setUp(self):
        """set up test files"""
        self.dir = to_str(tempfile.mkdtemp())
        self.config = os.path.join(self.dir, 'cirrus.conf')
        write_cirrus_conf(self.config,
            **{
                'package': {'name': 'cirrus_unittest', 'version': '1.2.3'},
                'gitflow': {'develop_branch': 'develop', 'release_branch_prefix': 'release/'},
                }
            )
        self.harness = CirrusConfigurationHarness('cirrus.release.load_configuration', self.config)
        self.harness.setUp()
        self.harness_utils = CirrusConfigurationHarness('cirrus.release_utils.load_configuration', self.config)
        self.harness_utils.setUp()
        self.patch_pull = mock.patch('cirrus.release.checkout_and_pull')
        self.patch_branch = mock.patch('cirrus.release.branch')
        self.patch_commit = mock.patch('cirrus.release.commit_files_optional_push')
        self.mock_pull = self.patch_pull.start()
        self.mock_branch = self.patch_branch.start()
        self.mock_commit = self.patch_commit.start()

    def tearDown(self):
        self.patch_pull.stop()
        self.patch_branch.stop()
        self.patch_commit.stop()
        self.harness.tearDown()
        self.harness_utils.tearDown()
        if os.path.exists(self.dir):
            os.system('rm -rf {0}'.format(self.dir))

    @mock.patch('cirrus.release.has_unstaged_changes')
    def test_new_release(self, mock_unstaged):
        """
        _test_new_release_

        """
        mock_unstaged.return_value = False
        opts = mock.Mock()
        opts.micro = True
        opts.major = False
        opts.minor = False
        opts.nightly = False
        opts.bump = None
        opts.skip_existing = False

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
        self.assertEqual(self.mock_commit.call_args[0][2], False)
        self.assertEqual(self.mock_commit.call_args[0][3], 'cirrus.conf')

    @mock.patch('cirrus.release.has_unstaged_changes')
    @mock.patch('cirrus.release.unmerged_releases')
    def test_new_release_skip_existing(self, mock_unmerged, mock_unstaged):
        """
        _test_new_release_

        """
        mock_unstaged.return_value = False
        mock_unmerged.return_value = ['1.2.4']
        opts = mock.Mock()
        opts.micro = True
        opts.major = False
        opts.minor = False
        opts.nightly = False
        opts.bump = None
        opts.skip_existing = True

        # should create a new minor release, editing
        # the cirrus config in the test dir
        new_release(opts)

        # verify new version
        new_conf = Configuration(self.config)
        new_conf.load()
        self.assertEqual(new_conf.package_version(), '1.2.5')

        self.failUnless(self.mock_pull.called)
        self.assertEqual(self.mock_pull.call_args[0][1], 'develop')
        self.failUnless(self.mock_branch.called)
        self.assertEqual(self.mock_branch.call_args[0][1], 'release/1.2.5')
        self.failUnless(self.mock_commit.called)
        self.assertEqual(self.mock_commit.call_args[0][2], False)
        self.assertEqual(self.mock_commit.call_args[0][3], 'cirrus.conf')

    @mock.patch('cirrus.release.has_unstaged_changes')
    @mock.patch('cirrus.release_utils.datetime')
    def test_new_nightly_release(self, mock_dt, mock_unstaged):
        """
        _test_new_release_

        """
        mock_ts = mock.Mock()
        mock_ts.strftime = mock.Mock(return_value="TIMESTAMP")
        mock_now = mock.Mock(return_value=mock_ts)
        mock_dt.datetime=mock.Mock()
        mock_dt.datetime.now = mock_now
        mock_unstaged.return_value = False
        opts = mock.Mock()
        opts.micro = False
        opts.major = False
        opts.minor = False
        opts.nightly = True
        opts.bump = None
        opts.skip_existing = False

        # should create a new minor release, editing
        # the cirrus config in the test dir
        new_release(opts)

        # verify new version
        new_conf = Configuration(self.config)
        new_conf.load()
        self.assertEqual(new_conf.package_version(), '1.2.3-nightly-TIMESTAMP')

        self.failUnless(self.mock_pull.called)
        self.assertEqual(self.mock_pull.call_args[0][1], 'develop')
        self.failUnless(self.mock_branch.called)
        self.assertEqual(self.mock_branch.call_args[0][1], 'release/1.2.3-nightly-TIMESTAMP')
        self.failUnless(self.mock_commit.called)
        self.assertEqual(self.mock_commit.call_args[0][2], False)
        self.assertEqual(self.mock_commit.call_args[0][3], 'cirrus.conf')


    @mock.patch('cirrus.release.has_unstaged_changes')
    @mock.patch('cirrus.release.bump_package')
    def test_new_release_bump(self, mock_bump, mock_unstaged):
        """
        _test_new_release_

        """
        mock_unstaged.return_value = False
        opts = mock.Mock()
        opts.micro = True
        opts.major = False
        opts.minor = False
        opts.nightly = False
        opts.skip_existing = False
        opts.bump = [['womp', '1.2.3'], ['wibble', '3.4.5']]

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
        self.assertEqual(self.mock_commit.call_args[0][2], False)
        self.assertEqual(self.mock_commit.call_args[0][3], 'cirrus.conf')

        self.assertEqual(mock_bump.call_count, 2)

    @mock.patch('cirrus.release.has_unstaged_changes')
    def test_new_release_unstaged(self, mock_unstaged):
        """
        test new release fails on unstaged changes

        """
        mock_unstaged.return_value = True
        opts = mock.Mock()
        opts.micro = True
        opts.major = False
        opts.minor = False
        opts.nightly = False
        opts.bump = None
        opts.skip_existing = False
        self.assertRaises(RuntimeError, new_release, opts)


class ReleaseCleanupCommandTest(unittest.TestCase):
    """
    Test Case for cleanup function
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
        self.patch_ghc = mock.patch('cirrus.release.GitHubContext')
        self.mock_ghc = self.patch_ghc.start()
        self.mock_ctx = mock.Mock()
        self.mock_instance = mock.Mock()
        self.mock_instance.delete_branch = mock.Mock()
        self.mock_ctx.__enter__ = mock.Mock(return_value=self.mock_instance)
        self.mock_ctx.__exit__ = mock.Mock()

        self.mock_ghc.return_value=self.mock_ctx

    def tearDown(self):
        self.patch_ghc.stop()
        self.harness.tearDown()
        if os.path.exists(self.dir):
            os.system('rm -rf {0}'.format(self.dir))

    def test_cleanup_command(self):
        """test cleanup"""
        opts = mock.Mock()
        opts.no_remote = False
        opts.version = None

        cleanup_release(opts)
        self.failUnless(self.mock_ghc.called)
        self.failUnless(self.mock_instance.delete_branch.called)
        self.mock_instance.delete_branch.assert_has_calls([mock.call('release/1.2.3', True)])

        self.mock_instance.reset_mock()
        opts.no_remote = True
        opts.version = '4.5.6'
        cleanup_release(opts)
        self.failUnless(self.mock_instance.delete_branch.called)
        self.mock_instance.delete_branch.assert_has_calls([mock.call('release/4.5.6', False)])

        self.mock_instance.reset_mock()
        opts.no_remote = False
        opts.version = 'release/7.8.9'
        cleanup_release(opts)
        self.failUnless(self.mock_instance.delete_branch.called)
        self.mock_instance.delete_branch.assert_has_calls([mock.call('release/7.8.9', True)])


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


class ReleaseUploadTest(unittest.TestCase):
    """unittest coverage for upload command using plugins"""
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
        self.artifact_name = artifact_name(self.harness.config)

    def tearDown(self):
        self.harness.tearDown()

    def test_missing_build_artifact(self):
        """test throws if build artifact not found"""
        opts = mock.Mock()
        self.assertRaises(RuntimeError, upload_release, opts)

    @mock.patch('cirrus.release.os.path.exists')
    @mock.patch('cirrus.release.get_plugin')
    def test_upload_plugin(self, mock_plugin, mock_exists):
        """test call with well behaved plugin"""
        plugin = mock.Mock()
        plugin.upload = mock.Mock()
        mock_exists.return_value = True
        mock_plugin.return_value = plugin
        opts = mock.Mock()
        opts.plugin = 'pypi'
        opts.test = False
        upload_release(opts)
        self.failUnless(plugin.upload.called)
        plugin.upload.assert_has_calls(
            [mock.call(opts, self.artifact_name)]
        )

    @mock.patch('cirrus.release.os.path.exists')
    @mock.patch('cirrus.release.get_plugin')
    def test_upload_plugin_test_mode(self, mock_plugin, mock_exists):
        plugin = mock.Mock()
        plugin.upload = mock.Mock()
        mock_exists.return_value = True
        mock_plugin.return_value = plugin
        opts = mock.Mock()
        opts.plugin = 'pypi'
        opts.test = True
        upload_release(opts)
        self.failUnless(not plugin.upload.called)

    @mock.patch('cirrus.release.os.path.exists')
    def test_upload_bad_plugin(self, mock_exists):
        """test with missing plugin"""
        mock_exists.return_value = True
        opts = mock.Mock()
        opts.plugin = 'womp'
        opts.test = True
        self.assertRaises(FactoryError, upload_release, opts)



if __name__ == '__main__':
    unittest.main()
