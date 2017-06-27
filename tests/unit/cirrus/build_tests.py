#!/usr/bin/env python
"""
build command test coverage
"""

import unittest
import mock

from cirrus.build import execute_build, build_parser


class BuildParserTests(unittest.TestCase):
    """test build_parser"""

    def test_build_parser(self):
        """test parser setup"""
        argv = ['build']
        opts = build_parser(argv)
        self.assertEqual(opts.clean, False)
        self.assertEqual(opts.command, 'build')
        self.assertEqual(opts.docs, None)
        self.assertEqual(opts.extras, None)
        self.assertEqual(opts.nosetupdevelop, False)
        self.assertEqual(opts.upgrade, False)

        argv = ['build', '--no-setup-develop']
        opts = build_parser(argv)
        self.failUnless(opts.nosetupdevelop)

        argv = [
            'build',
            '--extra-requirements',
            'test-requirements.txt',
            'other-requirements.txt'
        ]
        opts = build_parser(argv)
        self.assertEqual(
            opts.extras,
            ['test-requirements.txt', 'other-requirements.txt']
        )


class BuildCommandTests(unittest.TestCase):
    """test coverage for build command code"""
    def setUp(self):
        """set up patchers and mocks"""
        self.conf_patcher = mock.patch('cirrus.build.load_configuration')
        self.local_patcher = mock.patch('cirrus.build.local')
        self.os_path_exists_patcher = mock.patch('cirrus.build.os.path.exists')
        self.pypi_auth_patcher = mock.patch('cirrus.build.get_pypi_auth')
        self.cirrus_home_patcher = mock.patch('cirrus.build.repo_directory')
        self.pypirc_patcher = mock.patch('cirrus.build.PypircFile')

        self.build_params = {}
        self.pypi_url_value = None

        self.mock_pypirc_inst = mock.Mock()
        self.mock_pypirc_inst.index_servers = []

        self.mock_load_conf = self.conf_patcher.start()
        self.mock_conf = mock.Mock()
        self.mock_load_conf.return_value = self.mock_conf
        self.mock_conf.get = mock.Mock()
        self.mock_conf.get.return_value = self.build_params
        self.mock_conf.pypi_url = mock.Mock()
        self.mock_conf.pypi_url.return_value = self.pypi_url_value
        self.mock_conf.pip_options = mock.Mock(return_value=None)
        self.mock_local = self.local_patcher.start()
        self.mock_os_exists = self.os_path_exists_patcher.start()
        self.mock_os_exists.return_value = False
        self.mock_pypi_auth = self.pypi_auth_patcher.start()
        self.mock_cirrus_home = self.cirrus_home_patcher.start()
        self.mock_cirrus_home.return_value = 'CIRRUS_HOME'
        self.mock_pypirc = self.pypirc_patcher.start()
        self.mock_pypirc.return_value = self.mock_pypirc_inst

        self.mock_pypi_auth.return_value = {
            'username': 'PYPIUSERNAME',
            'ssh_username': 'SSHUSERNAME',
            'ssh_key': 'SSHKEY',
            'token': 'TOKEN'
        }

    def tearDown(self):
        self.conf_patcher.stop()
        self.local_patcher.stop()
        self.os_path_exists_patcher.stop()
        self.pypi_auth_patcher.stop()
        self.cirrus_home_patcher.stop()
        self.pypirc_patcher.stop()

    def test_execute_build_default_pypi(self):
        """test execute_build with default pypi settings"""
        opts = mock.Mock()
        opts.clean = False
        opts.upgrade = False
        opts.extras = []
        opts.nosetupdevelop = False
        opts.use_venv = None
        opts.python = None

        execute_build(opts)

        self.mock_local.assert_has_calls([
            mock.call('virtualenv CIRRUS_HOME/venv'),
            mock.call('CIRRUS_HOME/venv/bin/pip install -r requirements.txt'),
            mock.call('. CIRRUS_HOME/venv/bin/activate && python setup.py develop')
        ])

    @mock.patch('cirrus.build.is_anaconda')
    def test_execute_build_default_pypi_conda(self, mock_ana):
        """test execute_build with default pypi settings"""
        mock_ana.return_value = True
        opts = mock.Mock()
        opts.clean = False
        opts.upgrade = False
        opts.extras = []
        opts.nosetupdevelop = False
        opts.use_venv = None
        opts.python = None

        execute_build(opts)

        self.mock_local.assert_has_calls([
            mock.call('conda create -y -m -p CIRRUS_HOME/venv pip virtualenv'),
            mock.call('CIRRUS_HOME/venv/bin/pip install -r requirements.txt'),
            mock.call('source CIRRUS_HOME/venv/bin/activate CIRRUS_HOME/venv && python setup.py develop')
        ])



    def test_execute_build_default_pypi_custom_venv(self):
        """test execute_build with default pypi settings"""
        opts = mock.Mock()
        opts.clean = False
        opts.upgrade = False
        opts.extras = []
        opts.nosetupdevelop = False
        opts.use_venv = "CUSTOM_VENV"
        opts.python = None

        execute_build(opts)

        self.mock_local.assert_has_calls([
            mock.call('CUSTOM_VENV CIRRUS_HOME/venv'),
            mock.call('CIRRUS_HOME/venv/bin/pip install -r requirements.txt'),
            mock.call('. CIRRUS_HOME/venv/bin/activate && python setup.py develop')
        ])

    def test_execute_build_with_python_(self):
        """test execute_build with default pypi settings, -p option"""
        opts = mock.Mock()
        opts.clean = False
        opts.upgrade = False
        opts.extras = []
        opts.nosetupdevelop = False
        opts.use_venv = None
        opts.python = "python3"

        execute_build(opts)

        self.mock_local.assert_has_calls([
            mock.call('virtualenv -p python3  CIRRUS_HOME/venv'),
            mock.call('CIRRUS_HOME/venv/bin/pip install -r requirements.txt'),
            mock.call('. CIRRUS_HOME/venv/bin/activate && python setup.py develop')
        ])

    def test_execute_build_pypirc(self):
        """test execute_build with pypirc provided settings"""
        opts = mock.Mock()
        opts.clean = False
        opts.upgrade = False
        opts.extras = []
        opts.nosetupdevelop = False
        opts.use_venv = None
        opts.python = None

        self.mock_conf.pypi_url.return_value = "dev"
        self.mock_pypirc_inst.index_servers = ['dev']
        self.mock_pypirc_inst.get_pypi_url = mock.Mock(return_value="DEVPYPIURL")
        execute_build(opts)

        self.mock_local.assert_has_calls([
            mock.call('virtualenv CIRRUS_HOME/venv'),
            mock.call('CIRRUS_HOME/venv/bin/pip install -i DEVPYPIURL -r requirements.txt'),
            mock.call('. CIRRUS_HOME/venv/bin/activate && python setup.py develop')
        ])

    def test_execute_build_default_pypi_pip_options(self):
        """test execute_build with default pypi settings"""
        opts = mock.Mock()
        opts.clean = False
        opts.upgrade = False
        opts.extras = []
        opts.nosetupdevelop = False
        opts.use_venv = None
        opts.python = None
        self.mock_conf.pip_options.return_value = "PIPOPTIONS"
        execute_build(opts)

        self.mock_local.assert_has_calls([
            mock.call('virtualenv CIRRUS_HOME/venv'),
            mock.call('CIRRUS_HOME/venv/bin/pip install -r requirements.txt PIPOPTIONS '),
            mock.call('. CIRRUS_HOME/venv/bin/activate && python setup.py develop')
        ])

    def test_execute_build_default_pypi_upgrade(self):
        """test execute_build with default pypi settings and upgrade"""
        opts = mock.Mock()
        opts.clean = False
        opts.upgrade = True
        opts.extras = []
        opts.use_venv = None
        opts.python = None
        opts.nosetupdevelop = False

        execute_build(opts)

        self.mock_local.assert_has_calls([
            mock.call('virtualenv CIRRUS_HOME/venv'),
            mock.call('CIRRUS_HOME/venv/bin/pip install --upgrade -r requirements.txt'),
            mock.call('. CIRRUS_HOME/venv/bin/activate && python setup.py develop')
        ])

    def test_execute_build_with_extras(self):
        """test execute build with extra reqs"""
        opts = mock.Mock()
        opts.clean = False
        opts.upgrade = False
        opts.use_venv = None
        opts.python = None
        opts.extras = ['test-requirements.txt']
        opts.nosetupdevelop = False
        execute_build(opts)
        self.mock_local.assert_has_calls([
            mock.call('virtualenv CIRRUS_HOME/venv'),
            mock.call('CIRRUS_HOME/venv/bin/pip install -r requirements.txt'),
            mock.call('CIRRUS_HOME/venv/bin/pip install -r test-requirements.txt'),
            mock.call('. CIRRUS_HOME/venv/bin/activate && python setup.py develop')
        ])

    def test_execute_build_with_nosetupdevelop(self):
        """test nosetupdevelop option"""
        opts = mock.Mock()
        opts.clean = False
        opts.extras = []
        opts.upgrade = False
        opts.use_venv = None
        opts.python = None
        opts.nosetupdevelop = True

        execute_build(opts)
        self.mock_local.assert_has_calls([
            mock.call('virtualenv CIRRUS_HOME/venv'),
            mock.call('CIRRUS_HOME/venv/bin/pip install -r requirements.txt')
        ])

    def test_execute_build_with_pypi(self):
        """test execute build with pypi opts"""
        opts = mock.Mock()
        opts.clean = False
        opts.extras = []
        opts.upgrade = False
        opts.use_venv = None
        opts.python = None
        opts.nosetupdevelop = False
        self.mock_conf.pypi_url.return_value = "PYPIURL"

        execute_build(opts)

        self.mock_local.assert_has_calls([
            mock.call('virtualenv CIRRUS_HOME/venv'),
            mock.call('CIRRUS_HOME/venv/bin/pip install -i https://PYPIUSERNAME:TOKEN@PYPIURL/simple -r requirements.txt'),
            mock.call('. CIRRUS_HOME/venv/bin/activate && python setup.py develop')

        ])

    def test_execute_build_with_pypi_upgrade(self):
        """test execute build with pypi opts and upgrade"""
        opts = mock.Mock()
        opts.clean = False
        opts.extras = []
        opts.use_venv = None
        opts.nosetupdevelop = False
        opts.upgrade = True
        opts.python = None
        self.mock_conf.pypi_url.return_value = "PYPIURL"

        execute_build(opts)

        self.mock_local.assert_has_calls([
            mock.call('virtualenv CIRRUS_HOME/venv'),
            mock.call('CIRRUS_HOME/venv/bin/pip install -i https://PYPIUSERNAME:TOKEN@PYPIURL/simple --upgrade -r requirements.txt'),
            mock.call('. CIRRUS_HOME/venv/bin/activate && python setup.py develop')
        ])


if __name__ == '__main__':
    unittest.main()
