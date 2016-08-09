#!/usr/bin/env python
"""tests for package commands """
import unittest
import mock
import os
import tempfile
import ConfigParser

from cirrus.package import (
    create_files,
    setup_branches,
    commit_and_tag,
    build_parser,
    init_package

)


class BuildParserTest(unittest.TestCase):
    """test for cli parser"""
    def test_build_parser(self):
        argslist = ['init']
        self.assertRaises(SystemExit, build_parser, argslist)

        argslist = ['init', '-p', 'throwaway', '-s', 'src']
        opts = build_parser(argslist)
        self.assertEqual(opts.source, 'src')
        self.assertEqual(opts.package, 'throwaway')
        self.assertEqual(opts.master, 'master')
        self.assertEqual(opts.develop, 'develop')


class GitFunctionTests(unittest.TestCase):
    """
    tests for git util functions
    """
    def setUp(self):
        """
        set up for tests
        """
        self.tempdir = tempfile.mkdtemp()
        self.repo = os.path.join(self.tempdir, 'throwaway')
        os.mkdir(self.repo)

        self.patch_working_dir = mock.patch('cirrus.package.working_dir')
        self.mock_wd = self.patch_working_dir.start()

    def tearDown(self):
        self.patch_working_dir.stop()
        if os.path.exists(self.tempdir):
            os.system('rm -rf {}'.format(self.tempdir))

    @mock.patch('cirrus.package.branch')
    @mock.patch('cirrus.package.push')
    @mock.patch('cirrus.package.get_active_branch')
    def test_setup_branches(self, mock_active, mock_push, mock_branch):
        """test setup_branches"""
        opts = mock.Mock()
        opts.no_remote = False
        opts.repo = self.repo
        mock_active.return_value = 'mock_develop'

        setup_branches(opts)
        self.assertEqual(mock_branch.call_count, 2)
        self.failUnless(mock_push.called)
        self.failUnless(mock_active.called)

        mock_push.reset_mock()
        opts.no_remote = True
        setup_branches(opts)
        self.failUnless(not mock_push.called)

    @mock.patch('cirrus.package.commit_files_optional_push')
    @mock.patch('cirrus.package.get_tags')
    @mock.patch('cirrus.package.tag_release')
    @mock.patch('cirrus.package.branch')
    def test_commit_and_tag(self, mock_branch, mock_tag_rel, mock_tags, mock_commit):
        opts = mock.Mock()
        opts.no_remote = False
        opts.repo = self.repo
        opts.master = 'master'
        opts.version = '0.0.0'

        #tag doesnt exist
        mock_tags.return_value = ['0.0.1']
        commit_and_tag(opts, 'file1', 'file2')

        self.failUnless(mock_commit.called)
        mock_commit.assert_has_calls([
            mock.call(
                self.repo,
                'git cirrus package init',
                True,
                'file1',
                'file2'
            )
        ])
        self.failUnless(mock_tags.called)
        self.failUnless(mock_tag_rel.called)
        self.failUnless(mock_branch.called)

        # tag exists
        opts.version = '0.0.1'
        mock_tag_rel.reset_mock()
        commit_and_tag(opts, 'file1', 'file2')
        self.failUnless(not mock_tag_rel.called)

class CreateFilesTest(unittest.TestCase):
    """mocked create_files function tests"""
    def setUp(self):
        """
        set up for tests
        """
        self.tempdir = tempfile.mkdtemp()
        self.repo = os.path.join(self.tempdir, 'throwaway')
        src_dir = os.path.join(self.repo, 'src')
        os.mkdir(self.repo)
        os.mkdir(src_dir)
        init_file = os.path.join(src_dir, '__init__.py')
        with open(init_file, 'w') as handle:
            handle.write('# initfile\n')
            handle.write('__version__=\'0.0.0\'\n')

    def tearDown(self):
        if os.path.exists(self.tempdir):
            os.system('rm -rf {}'.format(self.tempdir))

    def test_create_files(self):
        """test create_files call and content of files"""
        opts = mock.Mock()
        opts.version_file = '__init__.py'
        opts.repo = self.repo
        opts.source = 'src'
        opts.version = '0.0.1'
        opts.templates = ['include steve/*']
        opts.history_file = 'HISTORY.md'
        opts.package = 'unittests'

        create_files(opts)

        dir_list = os.listdir(self.repo)
        self.failUnless('cirrus.conf' in dir_list)
        self.failUnless('HISTORY.md' in dir_list)
        self.failUnless('MANIFEST.in' in dir_list)
        self.failUnless('setup.py' in dir_list)

        cirrus_conf = os.path.join(self.repo, 'cirrus.conf')
        config = ConfigParser.RawConfigParser()
        config.read(cirrus_conf)
        self.assertEqual(config.get('package', 'name'), opts.package)
        self.assertEqual(config.get('package', 'version'), opts.version)

        history = os.path.join(self.repo, 'HISTORY.md')
        with open(history, 'r') as handle:
            self.failUnless('CIRRUS_HISTORY_SENTINEL' in handle.read())

        manifest = os.path.join(self.repo, 'MANIFEST.in')
        with open(manifest, 'r') as handle:
            content = handle.read()
            self.failUnless('include requirements.txt' in content)
            self.failUnless('include cirrus.conf' in content)
            self.failUnless('include steve/*' in content)


@unittest.skip("Integ test not unit test")
class PackageInitCommandIntegTest(unittest.TestCase):
    """test case for package init command """

    def setUp(self):
        """
        set up for tests
        """
        self.tempdir = tempfile.mkdtemp()
        self.repo = os.path.join(self.tempdir, 'throwaway')
        src_dir = os.path.join(self.repo, 'src')
        os.mkdir(self.repo)
        os.mkdir(src_dir)
        init_file = os.path.join(src_dir, '__init__.py')
        with open(init_file, 'w') as handle:
            handle.write('# initfile\n')
        cmd = (
            "cd {} && git init && "
            "git checkout -b master && "
            "git commit --allow-empty -m \"new repo\" "
        ).format(self.repo)
        os.system(cmd)

    def tearDown(self):
        if os.path.exists(self.tempdir):
            os.system('rm -rf {}'.format(self.tempdir))

    def test_init_command(self):
        """test the init command"""
        argslist = [
            'init', '-p', 'throwaway', '-r', self.repo,
            '--no-remote',
            '-s', 'src',
            '--templates', 'src/throwaway/templates/*'
        ]
        opts = build_parser(argslist)
        init_package(opts)
        conf = os.path.join(self.repo, 'cirrus.conf')
        self.failUnless(os.path.exists(conf))


if __name__ == '__main__':
    unittest.main()
