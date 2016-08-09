#!/usr/bin/env python
"""tests for package commands """
import unittest
import mock
import os
import tempfile
import ConfigParser

from cirrus.package import (
    create_files,
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


class InitFunctionsTest(unittest.TestCase):
    """mocked out init function tests"""
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
