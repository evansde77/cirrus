#!/usr/bin/env python
"""
docker command unittests
"""

import unittest
import mock

import cirrus.docker as dckr
from cirrus.configuration import Configuration
from subprocess import CalledProcessError


class DockerFunctionTests(unittest.TestCase):
    """
    test coverage for docker command module functions
    """

    def setUp(self):
        self.patcher = mock.patch('cirrus.docker.subprocess')
        self.version_patcher = mock.patch('cirrus.docker.get_docker_version')
        self.mock_subp = self.patcher.start()
        self.mock_get_docker_version = self.version_patcher.start()
        self.mock_get_docker_version.return_value = 'Docker version 1.12.0, build 8eab29e'
        self.mock_subp.STDOUT = 'STOUT'
        self.mock_check_output = mock.Mock()
        self.mock_check_output.return_value = 'SUBPROCESS OUT'
        self.mock_subp.check_output = self.mock_check_output
        self.mock_popen = mock.Mock()
        self.mock_subp.Popen = mock.Mock()
        self.mock_subp.Popen.return_value = self.mock_popen
        self.mock_popen.communicate = mock.Mock()
        self.mock_popen.communicate.return_value = ('STDOUT', 'STDERR')

        self.opts = mock.Mock()
        self.opts.login = False
        self.opts.directory = None
        self.opts.dockerstache_template = None
        self.opts.dockerstache_context = None
        self.opts.dockerstache_defaults = None
        self.opts.pre_script = None

        self.config = Configuration(None)
        self.config['package'] = {
            'version': '1.2.3',
            'name': 'unittesting'
        }
        self.config['docker'] = {
            'directory': 'vm/docker_image',
            'repo': 'unittesting'

        }
        self.config.credentials = mock.Mock()
        self.config.credentials.credential_map = mock.Mock()
        self.config.credentials.credential_map.return_value = {
            'github_credentials': {'github_user': 'steve', 'github_token': 'steves gh token'},
            'pypi_credentials': {'username': 'steve', 'token': 'steves pypi token'}
        }

    def tearDown(self):
        self.patcher.stop()
        self.version_patcher.stop()

    def test_docker_build(self):
        """test straight docker build call"""
        dckr.docker_build(self.opts, self.config)
        self.failUnless(self.mock_subp.check_output.called)
        self.mock_subp.check_output.assert_has_calls(
            mock.call(
                'docker build -t unittesting/unittesting:latest -t unittesting/unittesting:1.2.3 vm/docker_image',
                shell=True
            )
        )

    def test_docker_build_with_pre_script(self):
        """test straight docker build call"""
        self.opts.pre_script = "echo WOMP"
        dckr.docker_build(self.opts, self.config)
        self.failUnless(self.mock_subp.check_output.called)
        self.mock_subp.check_output.assert_has_calls(
            mock.call(
                'echo WOMP\ndocker build -t unittesting/unittesting:latest -t unittesting/unittesting:1.2.3 vm/docker_image',
                shell=True
            )
        )

    def test_docker_build_tag_opts(self):
        """test the _build_tag_opts helper function"""
        tag_opts = dckr._build_tag_opts(('hodor', '0.1.2', 'latest'))
        self.assertEqual(tag_opts, ['-t', 'hodor', '-t', '0.1.2', '-t', 'latest'])

    @mock.patch('cirrus.docker.ds')
    def test_docker_build_template(self, mock_ds):
        """test build with template"""
        mock_ds.run = mock.Mock()
        self.opts.dockerstache_template = 'template'
        self.opts.dockerstache_context = 'context'
        self.opts.dockerstache_defaults = 'defaults'
        dckr.docker_build(self.opts, self.config)
        self.failUnless(mock_ds.run.called)

        mock_ds.run.assert_has_calls(
            mock.call(
                output='vm/docker_image', context=None, defaults=None, input='template', extend_context=mock.ANY
            )
        )
        self.mock_subp.check_output.assert_has_calls(
            mock.call(
                'docker build -t unittesting/unittesting:latest -t unittesting/unittesting:1.2.3 vm/docker_image',
                shell=True

            )
        )

    def test_docker_build_login(self):
        """test build with login"""
        self.opts.login = True
        # no creds in config:
        self.assertRaises(SystemExit, dckr.docker_build, self.opts, self.config)

        self.config['docker']['docker_login_username'] = 'steve'
        self.config['docker']['docker_login_password'] = 'st3v3R0X'
        self.config['docker']['docker_login_email'] = 'steve@pbr.com'

        dckr.docker_build(self.opts, self.config)
        self.failUnless(self.mock_subp.check_output.called)
        self.mock_subp.check_output.assert_has_calls(
            [
                mock.call(['docker', 'login', '-u', 'steve', '-e', 'steve@pbr.com', '-p', 'st3v3R0X']),
                mock.call(
                    'docker build -t unittesting/unittesting:latest -t unittesting/unittesting:1.2.3 vm/docker_image',
                    shell=True
                )
            ]
        )

    def test_docker_push(self):
        """test plain docker push"""
        self.opts.tag = None
        self.opts.latest = False
        dckr.docker_push(self.opts, self.config)

        self.mock_subp.check_output.assert_has_calls(
            [
                mock.call(['docker', 'push', 'unittesting/unittesting:1.2.3']),
            ]
        )

    def test_docker_push_latest(self):
        """test plain docker push"""
        self.opts.tag = None
        self.opts.latest = True
        dckr.docker_push(self.opts, self.config)

        self.mock_subp.check_output.assert_has_calls(
            [
                mock.call(['docker', 'push', 'unittesting/unittesting:1.2.3']),
                mock.call(['docker', 'push', 'unittesting/unittesting:latest']),
            ]
        )

    def test_docker_push_login(self):
        """test push with login"""
        self.opts.login = True
        self.opts.tag = None
        self.config['docker']['docker_login_username'] = 'steve'
        self.config['docker']['docker_login_password'] = 'st3v3R0X'
        self.config['docker']['docker_login_email'] = 'steve@pbr.com'
        dckr.docker_push(self.opts, self.config)
        self.mock_subp.check_output.assert_has_calls(
            [
                mock.call(['docker', 'push', 'unittesting/unittesting:1.2.3'])
            ]
        )

    def test_docker_connection(self):
        """test is_docker_connected function called as expected"""
        dckr.is_docker_connected()
        self.mock_subp.check_output.assert_has_calls(
            [mock.call(['docker', 'info'], stderr='STOUT')])

    def test_docker_connection_success(self):
        """test successful docker daemon connection"""
        result = dckr.is_docker_connected()
        self.assertTrue(result)

    def test_docker_connection_error(self):
        """test failed docker daemon connection"""
        self.mock_subp.check_output.side_effect = CalledProcessError(
            1,
            ['docker', 'info'],
            'Cannot connect to the Docker daemon...')

        with self.assertRaises(CalledProcessError):
            result = dckr.is_docker_connected()
            self.assertFalse(result)


class DockerUtilTest(unittest.TestCase):
    """
    The DockerFunctionTests class patches too much (all of the subprocess module)
    As a result, things like subprocess.CalledProcessError are not caught properly
    by self.assertRaises
    Use this class to mock bits as needed.
    """

    @mock.patch('cirrus.docker.subprocess.check_output')
    def test_get_docker_version(self, mock_check_output):
        mock_check_output.return_value = 'Docker version 1.12.0, build 8eab29e'
        version = dckr.get_docker_version()
        self.assertEqual(version, 'Docker version 1.12.0, build 8eab29e')

    @mock.patch('cirrus.docker.subprocess.check_output')
    def test_get_docker_version_error(self, mock_check_output):
        """test that a subprocess error is caught/handled"""
        mock_check_output.side_effect = CalledProcessError(
            1,
            ['docker', '-v'],
            'Some error')

        with self.assertRaises(dckr.DockerVersionError):
            dckr.get_docker_version()

    def test_match_docker_version_error(self):
        """test a docker version match against unexpected input"""
        with self.assertRaises(dckr.DockerVersionError):
            dckr.match_docker_version('-bash: docker: command not found')

    @mock.patch('cirrus.docker.get_docker_version')
    def test_is_docker_version_installed(self, mock_get_docker_version):
        """test docker version compare function"""
        mock_get_docker_version.return_value = 'Docker version 1.12.0, build 8eab29e'
        self.assertIs(dckr.is_docker_version_installed('1.10.0'), True)
        self.assertIs(dckr.is_docker_version_installed('1.10.1'), True)
        self.assertIs(dckr.is_docker_version_installed('1.11.0'), True)
        self.assertIs(dckr.is_docker_version_installed('1.13.0'), False)


if __name__ == '__main__':
    unittest.main()
