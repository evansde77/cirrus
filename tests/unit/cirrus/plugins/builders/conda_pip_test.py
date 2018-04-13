#!/usr/bin/env python
"""
tests for VirtualenvPip builder plugin

"""

import unittest
import mock
import tempfile
import os

from cirrus.build import FACTORY


class CondaPipBuilderTest(unittest.TestCase):

    @mock.patch('cirrus.builder_plugin.load_configuration')
    @mock.patch('cirrus.builder_plugin.repo_directory')
    @mock.patch('cirrus.plugins.builders.conda_pip.local')
    @mock.patch('cirrus.builder_plugin.local')
    @mock.patch('cirrus.plugins.builders.conda_pip.build_pip_command')
    @mock.patch('cirrus.plugins.builders.conda_pip.os.path.exists')
    def test_builder(self, mock_ospe, mock_pip, mock_base_local, mock_local, mock_repo_dir, mock_load_conf):
        mock_pip.return_value = "PIP_COMMAND"
        mock_repo_dir.return_value = "REPO"
        mock_ospe.return_value = True
        mock_conf = mock.Mock(name="load_configuration")
        mock_conf.get = mock.Mock(return_value={
            'build': {'builder': 'conf'},
            'extra_requirements': ['test-requirements.txt', 'more-reqs.txt']
        })
        mock_load_conf.return_value = mock_conf
        plugin = FACTORY('CondaPip')
        plugin.create(clean=True, python='3.5')
        plugin.activate()
        mock_base_local.assert_has_calls([
            mock.call('source REPO/venv/bin/activate REPO/venv && python setup.py develop')
        ])

        mock_local.assert_has_calls([
            mock.call('conda remove --all -y -p REPO/venv'),
            mock.call('PIP_COMMAND'),
            mock.call('PIP_COMMAND'),
            mock.call('PIP_COMMAND')
        ])
        mock_base_local.reset_mock()
        plugin.create(clean=True, nosetupdevelop=True)
        self.failUnless(not mock_base_local.called)

    @mock.patch('cirrus.builder_plugin.load_configuration')
    @mock.patch('cirrus.builder_plugin.repo_directory')
    @mock.patch('cirrus.plugins.builders.conda_pip.local')
    @mock.patch('cirrus.builder_plugin.local')
    @mock.patch('cirrus.plugins.builders.conda_pip.build_pip_command')
    @mock.patch('cirrus.plugins.builders.conda_pip.os.path.exists')
    def test_activate(self, mock_ospe, mock_pip, mock_base_local, mock_local, mock_repo_dir, mock_load_conf):
        mock_pip.return_value = "PIP_COMMAND"
        mock_repo_dir.return_value = "REPO"
        mock_ospe.return_value = True
        mock_conf = mock.Mock(name="load_configuration")
        mock_conf.get = mock.Mock(return_value={
            'build': {'builder': 'conf'},
            'extra_requirements': ['test-requirements.txt', 'more-reqs.txt']
        })
        mock_load_conf.return_value = mock_conf
        plugin = FACTORY('CondaPip')

        self.assertEqual(
            plugin.activate(),
            "source REPO/venv/bin/activate REPO/venv"
        )
        mock_ospe.return_value = False
        self.assertEqual(plugin.activate(), "source activate REPO/venv")


    @mock.patch('cirrus.builder_plugin.load_configuration')
    @mock.patch('cirrus.builder_plugin.repo_directory')
    @mock.patch('cirrus.plugins.builders.conda_pip.local')
    @mock.patch('cirrus.builder_plugin.local')
    @mock.patch('cirrus.plugins.builders.conda_pip.build_pip_command')
    @mock.patch('cirrus.plugins.builders.conda_pip.os.path.exists')
    @mock.patch('cirrus.plugins.builders.conda_pip.is_anaconda_5')
    @mock.patch('cirrus.plugins.builders.conda_pip.find_conda_setup_script')
    def test_activate_conda5(self, mock_find_conda, mock_is_5, mock_ospe, mock_pip, mock_base_local, mock_local, mock_repo_dir, mock_load_conf):
        mock_pip.return_value = "PIP_COMMAND"
        mock_repo_dir.return_value = "REPO"
        mock_ospe.return_value = True
        mock_is_5.return_value = True
        mock_find_conda.return_value = "/blah/conda/wonda/conda.sh"
        mock_conf = mock.Mock(name="load_configuration")
        mock_conf.get = mock.Mock(return_value={
            'build': {'builder': 'conf'},
            'extra_requirements': ['test-requirements.txt', 'more-reqs.txt']
        })
        mock_load_conf.return_value = mock_conf
        plugin = FACTORY('CondaPip')

        self.assertEqual(
            plugin.activate(),
            " . /blah/conda/wonda/conda.sh && conda  REPO/venv/bin/activate REPO/venv"
        )
        mock_ospe.return_value = False
        self.assertEqual(plugin.activate(), " . /blah/conda/wonda/conda.sh && conda  activate REPO/venv")

    @mock.patch('cirrus.builder_plugin.load_configuration')
    @mock.patch('cirrus.builder_plugin.repo_directory')
    @mock.patch('cirrus.plugins.builders.conda_pip.local')
    @mock.patch('cirrus.builder_plugin.local')
    @mock.patch('cirrus.plugins.builders.conda_pip.build_pip_command')
    @mock.patch('cirrus.plugins.builders.conda_pip.os.path.exists')
    def test_builder_python_bin(self, mock_ospe, mock_pip, mock_base_local, mock_local, mock_repo_dir, mock_load_conf):
        mock_pip.return_value = "PIP_COMMAND"
        mock_repo_dir.return_value = "REPO"
        mock_ospe.return_value = False
        mock_conf = mock.Mock(name="load_configuration")
        mock_conf.get = mock.Mock(return_value={
            'build': {'builder': 'conf'},
            'extra_requirements': ['test-requirements.txt', 'more-reqs.txt'],
            'python': '6.7'
        })
        mock_load_conf.return_value = mock_conf
        plugin = FACTORY('CondaPip')
        self.assertEqual(plugin.python_bin, '6.7')
        self.assertEqual(plugin.python_bin_for_conda, '6.7')
        plugin.create()
        mock_local.assert_has_calls([
            mock.call('conda create -y -m -p REPO/venv pip virtualenv python=6.7')
        ])

        # verify that pythonX.Y format also works
        mock_local.reset_mock()
        mock_conf.get = mock.Mock(return_value={
            'build': {'builder': 'conf'},
            'extra_requirements': ['test-requirements.txt', 'more-reqs.txt'],
            'python': 'python6.7'
        })
        mock_load_conf.return_value = mock_conf
        plugin2 = FACTORY('CondaPip')
        self.assertEqual(plugin2.python_bin, 'python6.7')
        self.assertEqual(plugin2.python_bin_for_conda, '6.7')
        plugin2.create()
        mock_local.assert_has_calls([
            mock.call('conda create -y -m -p REPO/venv pip virtualenv python=6.7')
        ])

    @mock.patch('cirrus.builder_plugin.load_configuration')
    @mock.patch('cirrus.builder_plugin.repo_directory')
    @mock.patch('cirrus.plugins.builders.conda_pip.local')
    @mock.patch('cirrus.builder_plugin.local')
    @mock.patch('cirrus.plugins.builders.conda_pip.build_pip_command')
    def test_builder_errors(self, mock_pip, mock_base_local, mock_local, mock_repo_dir, mock_load_conf):
        mock_pip.return_value = "PIP_COMMAND"
        mock_repo_dir.return_value = "REPO"

        mock_local.side_effect = OSError("BOOM")

        mock_conf = mock.Mock(name="load_configuration")
        mock_conf.get = mock.Mock(return_value={
            'build': {'builder': 'conf'},
            'extra_requirements': ['test-requirements.txt', 'more-reqs.txt']
        })
        mock_load_conf.return_value = mock_conf
        plugin = FACTORY('CondaPip')
        self.assertRaises(OSError, plugin.create, clean=True)

        mock_local.side_effect = [None, None, OSError("BOOM")]
        self.assertRaises(OSError, plugin.create, clean=True)


if __name__ == '__main__':
    unittest.main()
