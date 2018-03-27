#!/usr/bin/env python
"""
tests for conda builder plugin

"""

import unittest
import mock

from cirrus.build import FACTORY


class CondaBuilderTest(unittest.TestCase):

    @mock.patch('cirrus.builder_plugin.load_configuration')
    @mock.patch('cirrus.builder_plugin.repo_directory')
    @mock.patch('cirrus.plugins.builders.conda.local')
    @mock.patch('cirrus.builder_plugin.local')
    @mock.patch('cirrus.plugins.builders.conda.os.path.exists')
    def test_builder(self, mock_ospe, mock_base_local, mock_local, mock_repo_dir, mock_load_conf):
        mock_repo_dir.return_value = "REPO"
        mock_ospe.return_value = True
        mock_conf = mock.Mock(name="load_configuration")
        mock_conf.get = mock.Mock(return_value={
            'build': {'builder': 'conf'},
            'extra_requirements': ['test-requirements.txt', 'more-reqs.txt']
        })
        mock_load_conf.return_value = mock_conf
        plugin = FACTORY('Conda')
        plugin.create(clean=True, python='3.5')
        plugin.activate()
        mock_base_local.assert_has_calls([
            mock.call('source REPO/venv/bin/activate REPO/venv && python setup.py develop')
        ])

        mock_local.assert_has_calls([
            mock.call('conda remove --all -y -p REPO/venv'),
            mock.call('conda install --no-update-dependencies  --yes --file requirements.txt'),
            mock.call('conda install   --yes --file test-requirements.txt'),
            mock.call('conda install   --yes --file more-reqs.txt')
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
        plugin = FACTORY('Conda')

        self.assertEqual(
            plugin.activate(),
            "source REPO/venv/bin/activate REPO/venv"
        )
        mock_ospe.return_value = False
        self.assertEqual(plugin.activate(), "source activate REPO/venv")

    @mock.patch('cirrus.builder_plugin.load_configuration')
    @mock.patch('cirrus.builder_plugin.repo_directory')
    @mock.patch('cirrus.plugins.builders.conda.local')
    @mock.patch('cirrus.builder_plugin.local')
    @mock.patch('cirrus.plugins.builders.conda.os.path.exists')
    def test_builder_channels(self, mock_ospe, mock_base_local, mock_local, mock_repo_dir, mock_load_conf):
        mock_repo_dir.return_value = "REPO"
        mock_ospe.return_value = True
        mock_conf = mock.Mock(name="load_configuration")
        mock_conf.get = mock.Mock(return_value={
            'build': {'builder': 'conf'},
            "conda_channels": ['conda-forge', 'ioam'],
            'extra_requirements': ['test-requirements.txt', 'more-reqs.txt']
        })
        mock_load_conf.return_value = mock_conf
        plugin = FACTORY('Conda')
        plugin.create(clean=True, python='3.5')
        plugin.activate()
        mock_base_local.assert_has_calls([
            mock.call('source REPO/venv/bin/activate REPO/venv && python setup.py develop')
        ])
        mock_local.assert_has_calls([
            mock.call('conda remove --all -y -p REPO/venv'),
            mock.call('conda install --no-update-dependencies  -c conda-forge -c ioam --yes --file requirements.txt'),
            mock.call('conda install   -c conda-forge -c ioam --yes --file test-requirements.txt'),
            mock.call('conda install   -c conda-forge -c ioam --yes --file more-reqs.txt')

        ])
        mock_base_local.reset_mock()
        plugin.create(clean=True, nosetupdevelop=True)
        self.failUnless(not mock_base_local.called)

    @mock.patch('cirrus.builder_plugin.load_configuration')
    @mock.patch('cirrus.builder_plugin.repo_directory')
    @mock.patch('cirrus.plugins.builders.conda.local')
    @mock.patch('cirrus.builder_plugin.local')
    def test_builder_errors(self, mock_base_local, mock_local, mock_repo_dir, mock_load_conf):
        mock_repo_dir.return_value = "REPO"

        mock_local.side_effect = OSError("BOOM")

        mock_conf = mock.Mock(name="load_configuration")
        mock_conf.get = mock.Mock(return_value={
            'build': {'builder': 'conf'},
            'extra_requirements': ['test-requirements.txt', 'more-reqs.txt']
        })
        mock_load_conf.return_value = mock_conf
        plugin = FACTORY('Conda')
        self.assertRaises(OSError, plugin.create, clean=True)

        mock_local.side_effect = [None, OSError("BOOM")]
        self.assertRaises(OSError, plugin.create, clean=True)

        mock_local.side_effect = [None, None, OSError("BOOM")]
        self.assertRaises(OSError, plugin.create, clean=True)


if __name__ == '__main__':
    unittest.main()
