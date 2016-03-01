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
        self.mock_subp = self.patcher.start()
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

        self.config = Configuration(None)
        self.config['package'] = {
            'version': '1.2.3',
            'name': 'unittesting'
        }
        self.config['docker'] = {
            'directory': 'vm/docker_image',
            'repo': 'unittesting'

        }

    def tearDown(self):
        self.patcher.stop()

    def test_docker_build(self):
        """test straight docker build call"""
        dckr.docker_build(self.opts, self.config)
        self.failUnless(self.mock_subp.check_output.called)
        self.mock_subp.check_output.assert_has_calls(
            mock.call(
                ['docker', 'build', '-t', 'unittesting/unittesting:1.2.3', 'vm/docker_image']
            )
        )

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
                output='vm/docker_image', context=None, defaults=None, input='template'
            )
        )
        self.mock_subp.check_output.assert_has_calls(
            mock.call(
                ['docker', 'build', '-t', 'unittesting/unittesting:1.2.3', 'vm/docker_image']
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
                mock.call(['docker', 'build', '-t', 'unittesting/unittesting:1.2.3', 'vm/docker_image'])
            ]
        )

    def test_docker_push(self):
        """test plain docker push"""
        self.opts.tag = None
        dckr.docker_push(self.opts, self.config)

        self.opts.tag = "herpderp"
        dckr.docker_push(self.opts, self.config)

        self.mock_subp.check_output.assert_has_calls(
            [
                mock.call(['docker', 'push', 'unittesting/unittesting:1.2.3']),
                mock.call(['docker', 'push', 'herpderp'])
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

if __name__ == '__main__':
    unittest.main()
