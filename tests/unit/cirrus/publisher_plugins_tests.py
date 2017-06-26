from cirrus._2to3 import builtins
import mock
import os
import tempfile
import unittest

import pluggage.registry

from cirrus.documentation_utils import doc_artifact_name

from .harnesses import CirrusConfigurationHarness, write_cirrus_conf


class FileServerPublisherTests(unittest.TestCase):
    """
    Test the doc_file_server publisher plugin.

    A test config is defined with the values required to publish
    documentation using the doc_file_server plugin which uses Fabric
    put to upload the doc artifact to a remote server

    """

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.config = os.path.join(self.dir, 'cirrus.conf')
        self.makefile_dir = os.path.join(self.dir, 'docs')
        self.artifact_dir = os.path.join(self.dir, 'artifacts')
        self.doc_dir = os.path.join(self.dir, 'docs/_build/html')
        write_cirrus_conf(self.config,
            **{
                'package': {'name': 'cirrus_unittest', 'version': '1.2.3'},
                'doc': {
                    'publisher': 'doc_file_server',
                    'sphinx_makefile_dir': self.doc_dir,
                    'sphinx_doc_dir': self.doc_dir,
                    'artifact_dir': self.artifact_dir
                },
                'doc_file_server': {
                    'doc_file_server_url': 'http://localhost:8080',
                    'doc_file_server_upload_path': '/path/to/upload/dir'
                }
            }
        )
        self.harness = CirrusConfigurationHarness('cirrus.publish_plugins.load_configuration', self.config)
        self.harness.setUp()

        self.harness.config.credentials = mock.Mock()
        self.harness.config.credentials.file_server_credentials = mock.Mock(
            return_value={
                'file_server_username': 'username',
                'file_server_keyfile': '/path/to/ssh/keyfile'
            }
        )

        self.doc_artifact_name = doc_artifact_name(self.harness.config)

    def tearDown(self):
        self.harness.tearDown()
        if os.path.exists(self.dir):
            os.system('rm -rf {0}'.format(self.dir))

    @mock.patch('cirrus.plugins.publishers.doc_file_server.put')
    def test_docs_file_server(self, m_fabric_put):
        """
        test docs_file_server publisher plugin makes put command with Fabric
        """
        factory = pluggage.registry.get_factory(
            'publish',
            load_modules=['cirrus.plugins.publishers']
        )
        plugin = factory('doc_file_server')

        plugin.publish(self.doc_artifact_name)

        self.assertTrue(m_fabric_put.called_once_with(
            self.doc_artifact_name, '/path/to/upload/dir', sudo=False))


class JenkinsPublisherTests(unittest.TestCase):
    """
    Test the jenkins publisher plugin.

    A test config is defined with the values required to publish
    documentation using the jenkins plugin which issues an API request
    to Jenkins which uploads the documentation artifact and required
    parameters to a Jenkins job.

    """

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.config = os.path.join(self.dir, 'cirrus.conf')
        self.makefile_dir = os.path.join(self.dir, 'docs')
        self.artifact_dir = os.path.join(self.dir, 'artifacts')
        self.doc_dir = os.path.join(self.dir, 'docs/_build/html')
        write_cirrus_conf(self.config,
            **{
                'package': {'name': 'cirrus_unittest', 'version': '1.2.3'},
                'doc': {
                    'publisher': 'jenkins',
                    'sphinx_makefile_dir': self.doc_dir,
                    'sphinx_doc_dir': self.doc_dir,
                    'artifact_dir': self.artifact_dir
                },
                'jenkins': {
                    'url': 'http://localhost:8080',
                    'doc_job': 'default',
                    'doc_var': 'ARCHIVE',
                    'arc_var': 'ARCNAME',
                    'extra_vars': True
                },
                'jenkins_docs_extra_vars': {
                    'PROJECT': 'cirrus_unittest'
                }
            }
        )
        self.harness = CirrusConfigurationHarness('cirrus.publish_plugins.load_configuration', self.config)
        self.harness.setUp()
        self.doc_artifact_name = doc_artifact_name(self.harness.config)

    def tearDown(self):
        self.harness.tearDown()
        if os.path.exists(self.dir):
            os.system('rm -rf {0}'.format(self.dir))

    @mock.patch('cirrus.plugins.jenkins.requests')
    @mock.patch('cirrus.plugins.jenkins.get_buildserver_auth')
    @mock.patch('cirrus.plugins.publishers.jenkins.MultipartEncoder')
    def test_jenkins(self, m_encoder, m_auth, m_requests):
        """
        test jenkins publisher plugin uses MultipartEncoder to encode form
        data which is then sent to Jenkins via a POST to the Jenkins /build
        endpoint
        """
        factory = pluggage.registry.get_factory(
            'publish',
            load_modules=['cirrus.plugins.publishers']
        )
        plugin = factory('jenkins')

        m_session = mock.Mock()
        m_requests.Session = mock.Mock(return_value=m_session)
        m_resp = mock.Mock()
        m_resp.status_code = 201
        m_session.post = mock.Mock(return_value=m_resp)

        with mock.patch('cirrus.plugins.publishers.jenkins.builtins.open') as m_open:

            plugin.publish(self.doc_artifact_name)

            self.assertEqual(m_encoder.call_count, 1)
            self.assertEqual(m_open.call_count, 1)
            self.assertEqual(m_session.post.call_count, 1)


if __name__ == '__main__':
    unittest.main()
