#!/usr/bin/env python
"""tests for package commands """
import unittest
import mock
import os
import tempfile

from cirrus.package import build_parser, init_package


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


class PackageInitCommandTest(unittest.TestCase):
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
