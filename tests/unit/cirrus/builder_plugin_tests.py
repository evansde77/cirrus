#!/usr/bin/env python
"""
test coverage for builder plugin
"""
import unittest
import mock

from cirrus.builder_plugin import Builder


class BuilderPluginTest(unittest.TestCase):
    """tests for base builder plugin"""
    @mock.patch('cirrus.builder_plugin.load_configuration')
    @mock.patch('cirrus.builder_plugin.repo_directory')
    @mock.patch('cirrus.builder_plugin.local')
    def test_plugin(self, mock_local, mock_repo_dir, mock_load_conf):
        """test the basic plugin calls"""
        mock_conf = mock.Mock()
        mock_conf.get = mock.Mock(return_value={
            'build': {'builder': 'conf'},
            'extra_requirements': ['test-requirements.txt', 'more-reqs.txt']
        })
        mock_load_conf.return_value = mock_conf
        mock_repo_dir.return_value = "REPO"
        plug = Builder()
        plug.clean()
        plug.create()
        plug.activate()
        self.assertEqual(plug.venv_path, 'REPO/venv')
        self.assertEqual(plug.extra_reqs, ['test-requirements.txt', 'more-reqs.txt'])

        plug.run_setup_develop()
        self.assertTrue(mock_local.called)
        mock_local.assert_has_calls([
            mock.call('None && python setup.py develop')
        ])

        plug.plugin_parser.add_argument('-w', type=int)
        extras = plug.process_extra_args(['-w', '1', '-x', '2'])
        self.assertTrue('w' in extras)
        self.assertEqual(extras['w'], 1)
        self.assertEqual(plug.str_to_list('a,b,c'), ['a', 'b', 'c'])

    @mock.patch('cirrus.builder_plugin.load_configuration')
    @mock.patch('cirrus.builder_plugin.repo_directory')
    @mock.patch('cirrus.builder_plugin.local')
    def test_python_bin(self, mock_local, mock_repo_dir, mock_load_conf):
        mock_conf = mock.Mock()
        mock_conf.get = mock.Mock(return_value={
            'build': {'builder': 'conf'},
            'extra_requirements': ['test-requirements.txt', 'more-reqs.txt'],
            'python': 'python6.7'
        })
        mock_load_conf.return_value = mock_conf
        mock_repo_dir.return_value = "REPO"

        plug = Builder()
        self.assertEqual(plug.python_bin, 'python6.7')
        self.assertEqual(plug.python_bin_for_venv, 'python6.7')
        self.assertEqual(plug.python_bin_for_conda, '6.7')

        mock_conf = mock.Mock()
        mock_conf.get = mock.Mock(return_value={
            'build': {'builder': 'conf'},
            'extra_requirements': ['test-requirements.txt', 'more-reqs.txt'],
            'python': '6.7'
        })
        mock_load_conf.return_value = mock_conf
        plug2 = Builder()
        self.assertEqual(plug2.python_bin, '6.7')
        self.assertEqual(plug2.python_bin_for_venv, 'python6.7')
        self.assertEqual(plug2.python_bin_for_conda, '6.7')

    @mock.patch('cirrus.builder_plugin.load_configuration')
    @mock.patch('cirrus.builder_plugin.repo_directory')
    @mock.patch('cirrus.builder_plugin.local')
    @mock.patch('cirrus.builder_plugin.subprocess')
    def test_python_version(self, mock_subp, mock_local, mock_repo_dir, mock_load_conf):
        mock_conf = mock.Mock()
        mock_conf.get = mock.Mock(return_value={
            'build': {'builder': 'conf'},
            'extra_requirements': ['test-requirements.txt', 'more-reqs.txt'],
            'python': 'python6.7'
        })
        mock_load_conf.return_value = mock_conf
        mock_repo_dir.return_value = "REPO"
        mock_subp.getoutput = mock.Mock(return_value="  Python 3.7.1  ")
        plug = Builder()
        v = plug.venv_python_version()
        self.assertEqual(v.major, 3)
        self.assertEqual(v.minor, 7)
        self.assertEqual(v.micro, 1)
        mock_subp.getoutput.return_value = "Python 3.6.4 :: Anaconda, Inc."
        v = plug.venv_python_version()
        self.assertEqual(v.major, 3)
        self.assertEqual(v.minor, 6)
        self.assertEqual(v.micro, 4)

if __name__ == '__main__':
    unittest.main()
