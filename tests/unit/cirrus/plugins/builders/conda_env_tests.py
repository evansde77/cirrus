#!/usr/bin/env python
"""
tests for conda environment builder plugin

"""

import unittest
import mock

from cirrus.build import FACTORY


class CondaEnvBuilderTest(unittest.TestCase):

    @mock.patch('cirrus.builder_plugin.load_configuration')
    @mock.patch('cirrus.builder_plugin.repo_directory')
    @mock.patch('cirrus.plugins.builders.conda_env.local')
    @mock.patch('cirrus.builder_plugin.local')
    @mock.patch('cirrus.plugins.builders.conda_env.os.path.exists')
    def test_builder(self, mock_ospe, mock_base_local, mock_local, mock_repo_dir, mock_load_conf):
        mock_repo_dir.return_value = "REPO"
        mock_ospe.return_value = True
        mock_conf = mock.Mock(name="load_configuration")
        mock_conf.get = mock.Mock(return_value={
            'build': {'builder': 'conf'},
            'extra_requirements': ['test-requirements.txt', 'more-reqs.txt']
        })
        mock_load_conf.return_value = mock_conf
        plugin = FACTORY('CondaEnv')
        plugin.create(clean=True, upgrade=True, python='3.5', environment='env.yaml')
        plugin.activate()
        mock_base_local.assert_has_calls([
            mock.call('source REPO/venv/bin/activate REPO/venv && python setup.py develop')
        ])

        mock_local.assert_has_calls([
            mock.call('conda remove --all -y -p REPO/venv'),
            mock.call('source REPO/venv/bin/activate REPO/venv && conda env update REPO/venv -f env.yaml')
        ])

        mock_base_local.reset_mock()
        plugin.create(clean=True, nosetupdevelop=True, environment='env.yaml')
        self.failUnless(not mock_base_local.called)

    @mock.patch('cirrus.builder_plugin.load_configuration')
    @mock.patch('cirrus.builder_plugin.repo_directory')
    @mock.patch('cirrus.plugins.builders.conda_env.local')
    @mock.patch('cirrus.builder_plugin.local')
    @mock.patch('cirrus.plugins.builders.conda_env.os.path.exists')
    def test_activate(self, mock_ospe, mock_base_local, mock_local, mock_repo_dir, mock_load_conf):
        mock_repo_dir.return_value = "REPO"
        mock_ospe.return_value = True
        mock_conf = mock.Mock(name="load_configuration")
        mock_conf.get = mock.Mock(return_value={
            'build': {'builder': 'conf'},
            'extra_requirements': ['test-requirements.txt', 'more-reqs.txt']
        })
        mock_load_conf.return_value = mock_conf
        plugin = FACTORY('CondaEnv')

        self.assertEqual(
            plugin.activate(),
            "source REPO/venv/bin/activate REPO/venv"
        )

        mock_ospe.return_value = False
        self.assertEqual(plugin.activate(), "source activate REPO/venv")

    @mock.patch('cirrus.builder_plugin.load_configuration')
    @mock.patch('cirrus.builder_plugin.repo_directory')
    @mock.patch('cirrus.plugins.builders.conda_env.local')
    @mock.patch('cirrus.builder_plugin.local')
    @mock.patch('cirrus.plugins.builders.conda_env.os.path.exists')
    def test_builder_new_conda(self, mock_ospe, mock_base_local, mock_local, mock_repo_dir, mock_load_conf):
        mock_repo_dir.return_value = "REPO"
        pe_results  = [True for x in range(17)]
        pe_results.extend([False, False])
        mock_ospe.side_effect = pe_results
        mock_conf = mock.Mock(name="load_configuration")
        mock_conf.get = mock.Mock(return_value={
            'build': {'builder': 'conf'},
            'extra_requirements': ['test-requirements.txt', 'more-reqs.txt']
        })
        mock_load_conf.return_value = mock_conf
        plugin = FACTORY('CondaEnv')
        plugin.create(clean=True, upgrade=True, python='3.5', environment='env.yaml')
        plugin.activate()
        mock_base_local.assert_has_calls([
            mock.call('source REPO/venv/bin/activate REPO/venv && python setup.py develop')
        ])

        mock_local.assert_has_calls([
            mock.call('conda remove --all -y -p REPO/venv'),
            mock.call('source REPO/venv/bin/activate REPO/venv && conda env update REPO/venv -f env.yaml')
        ])

        mock_base_local.reset_mock()
        plugin.create(clean=True, nosetupdevelop=True, environment='env.yaml')
        self.failUnless(not mock_base_local.called)

    @mock.patch('cirrus.builder_plugin.load_configuration')
    @mock.patch('cirrus.builder_plugin.repo_directory')
    @mock.patch('cirrus.plugins.builders.conda_env.local')
    @mock.patch('cirrus.builder_plugin.local')
    @mock.patch('cirrus.plugins.builders.conda_env.os.path.exists')
    def test_builder_extra_pip(self, mock_ospe, mock_base_local, mock_local, mock_repo_dir, mock_load_conf):
        mock_repo_dir.return_value = "REPO"
        mock_ospe.return_value = True
        mock_conf = mock.Mock(name="load_configuration")
        mock_conf.get = mock.Mock(return_value={
            'build': {'builder': 'conf'},
            'extra_pip_requirements': 'extra-pip-requirements.txt',
            'extra_requirements': ['test-requirements.txt', 'more-reqs.txt']
        })
        mock_conf.pip_options = mock.Mock(return_value="PIP_OPTIONS")
        mock_load_conf.return_value = mock_conf
        plugin = FACTORY('CondaEnv')
        plugin.create(clean=True, upgrade=True, python='3.5', environment='env.yaml')
        plugin.activate()
        mock_base_local.assert_has_calls([
            mock.call('source REPO/venv/bin/activate REPO/venv && python setup.py develop')
        ])

        mock_local.assert_has_calls([
            mock.call('conda remove --all -y -p REPO/venv'),
            mock.call('source REPO/venv/bin/activate REPO/venv && conda env update REPO/venv -f env.yaml'),
            mock.call('source REPO/venv/bin/activate REPO/venv && pip install -r extra-pip-requirements.txt PIP_OPTIONS')
        ])
        mock_base_local.reset_mock()
        plugin.create(clean=True, nosetupdevelop=True, environment='env.yaml')
        self.failUnless(not mock_base_local.called)

    @mock.patch('cirrus.builder_plugin.load_configuration')
    @mock.patch('cirrus.builder_plugin.repo_directory')
    @mock.patch('cirrus.plugins.builders.conda_env.local')
    @mock.patch('cirrus.builder_plugin.local')
    @mock.patch('cirrus.plugins.builders.conda_env.os.path.exists')
    def test_builder_extra_conda(self, mock_ospe, mock_base_local, mock_local, mock_repo_dir, mock_load_conf):
        mock_repo_dir.return_value = "REPO"
        mock_ospe.return_value = True
        mock_conf = mock.Mock(name="load_configuration")
        mock_conf.get = mock.Mock(return_value={
            'build': {'builder': 'conf'},
            'extra_conda_requirements': 'extra-conda-requirements.txt',
            'extra_requirements': ['test-requirements.txt', 'more-reqs.txt']
        })
        mock_conf.pip_options = mock.Mock(return_value="PIP_OPTIONS")
        mock_load_conf.return_value = mock_conf
        plugin = FACTORY('CondaEnv')
        plugin.create(clean=True, upgrade=True, python='3.5', environment='env.yaml')
        plugin.activate()
        mock_base_local.assert_has_calls([
            mock.call('source REPO/venv/bin/activate REPO/venv && python setup.py develop')
        ])

        mock_local.assert_has_calls([
            mock.call('conda remove --all -y -p REPO/venv'),
            mock.call('source REPO/venv/bin/activate REPO/venv && conda env update REPO/venv -f env.yaml'),
            mock.call('source REPO/venv/bin/activate REPO/venv && conda install REPO/venv -f extra-conda-requirements.txt')
        ])
        mock_base_local.reset_mock()
        plugin.create(clean=True, nosetupdevelop=True, environment='env.yaml')
        self.failUnless(not mock_base_local.called)

    @mock.patch('cirrus.builder_plugin.load_configuration')
    @mock.patch('cirrus.builder_plugin.repo_directory')
    @mock.patch('cirrus.plugins.builders.conda_env.local')
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
        plugin = FACTORY('CondaEnv')
        self.assertRaises(OSError, plugin.create, upgrade=True, clean=True, environment='env.yaml')

        mock_local.side_effect = [None, OSError("BOOM")]
        self.assertRaises(OSError, plugin.create, clean=True, upgrade=True, environment='env.yaml')





if __name__ == '__main__':
    unittest.main()
