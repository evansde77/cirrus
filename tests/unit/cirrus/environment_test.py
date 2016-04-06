#!/usr/bin/env python
"""
unittests for cirrus.environment module

"""

import os
import copy
import unittest
import mock
import tempfile

from cirrus.environment import cirrus_home
from cirrus.environment import virtualenv_home


class EnvironmentFunctionTests(unittest.TestCase):
    """
    test case for environment module functions

    """
    def setUp(self):
        """save/mock the os.environ settings"""
        self.cirrus_home = copy.deepcopy(os.environ.get('CIRRUS_HOME'))
        self.venv_home = copy.deepcopy(os.environ.get('VIRTUALENV_HOME'))
        os.environ['CIRRUS_HOME'] = "TESTVALUE"
        os.environ['VIRTUALENV_HOME'] = "TESTVALUE"

    def tearDown(self):
        """reset env vars"""
        if self.cirrus_home is not None:
            os.environ['CIRRUS_HOME'] = self.cirrus_home
        if self.venv_home is not None:
            os.environ['VIRTUALENV_HOME'] = self.venv_home

    def test_cirrus_home(self):
        """test cirrus home function"""

        home1 = cirrus_home()
        self.assertEqual(home1, 'TESTVALUE')
        del os.environ['CIRRUS_HOME']

        home2 = cirrus_home()
        self.assertNotEqual(home2, 'TESTVALUE')

    def test_venv_home(self):
        """test venv home function"""
        home1 = virtualenv_home()
        self.assertEqual(home1, 'TESTVALUE')
        del os.environ['VIRTUALENV_HOME']

        home2 = virtualenv_home()
        self.assertEqual(home2, 'TESTVALUE/venv')


class CleanEnvironmentTests(unittest.TestCase):

    def setUp(self):
        """save/mock the os.environ settings"""
        self.dir = tempfile.mkdtemp()
        self.venv_dir = os.path.join(
            self.dir, 'venv', 'lib', 'python2.7',
            'site-packages', 'cirrus', '__init__.py'
            )
        self.venv_dir_2 = os.path.join(
            self.dir, 'venv', 'cirrus', '__init__.py'
            )

    def tearDown(self):
        """reset env vars"""
        if os.path.exists(self.dir):
            os.system('rm -rf {}'.format(self.dir))

    @mock.patch('cirrus.environment.inspect.getsourcefile')
    @mock.patch('cirrus.environment.repo_directory')
    @mock.patch('cirrus.environment.os.environ')
    def test_cirrus_home_in_venv(self, mock_env, mock_repo, mock_srcfile):
        mock_env.get = mock.Mock()
        mock_env.get = mock.Mock()
        mock_env.get.return_value = None
        mock_env.__getitem__ = mock.Mock()
        mock_env.__getitem__.return_value = self.dir
        mock_env.__setitem__ = mock.Mock()
        mock_srcfile.return_value = self.venv_dir
        self.assertEqual(cirrus_home(), self.dir)
        self.failUnless(not mock_repo.called)
        self.failUnless(mock_env.__setitem__.called)

    @mock.patch('cirrus.environment.inspect.getsourcefile')
    @mock.patch('cirrus.environment.repo_directory')
    @mock.patch('cirrus.environment.os.environ')
    def test_cirrus_home_in_bad_repo(self, mock_env, mock_repo, mock_srcfile):
        """test no venv or repo"""
        mock_env.get = mock.Mock()
        mock_env.get = mock.Mock()
        mock_env.get.return_value = None
        mock_env.__getitem__ = mock.Mock()
        mock_env.__getitem__.return_value = self.dir
        mock_env.__setitem__ = mock.Mock()
        mock_srcfile.return_value = self.venv_dir_2
        mock_repo.return_value = None
        self.assertRaises(RuntimeError, cirrus_home)
        self.failUnless(not mock_env.__setitem__.called)

    @mock.patch('cirrus.environment.inspect.getsourcefile')
    @mock.patch('cirrus.environment.repo_directory')
    @mock.patch('cirrus.environment.os.environ')
    def test_cirrus_home_in_repo(self, mock_env, mock_repo, mock_srcfile):
        """test repo source file and no repo info"""
        mock_env.get = mock.Mock()
        mock_env.get.return_value = None
        mock_env.__getitem__ = mock.Mock()
        mock_env.__getitem__.return_value = None
        mock_env.__setitem__ = mock.Mock()
        mock_srcfile.return_value = self.venv_dir_2
        mock_repo.return_value = os.path.dirname(self.venv_dir_2)
        self.assertEqual(cirrus_home(), os.path.dirname(self.venv_dir_2))
        self.failUnless(mock_repo.called)
        self.failUnless(mock_env.__setitem__.called)


if __name__ == '__main__':
    unittest.main()
