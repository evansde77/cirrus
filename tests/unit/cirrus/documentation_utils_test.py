"""
documentation utils tests

"""
import __builtin__
import mock
import os
import tempfile
import unittest

from requests_toolbelt import MultipartEncoder

from cirrus.documentation_utils import doc_artifact_name
from cirrus.documentation_utils import build_docs
from cirrus.documentation_utils import build_doc_artifact
from cirrus.documentation_utils import upload_documentation

from harnesses import CirrusConfigurationHarness, write_cirrus_conf

class TestDocumentationUtils(unittest.TestCase):
    def setUp(self):
        """set up test files"""
        self.dir = tempfile.mkdtemp()
        self.config = os.path.join(self.dir, 'cirrus.conf')
        self.makefile_dir = os.path.join(self.dir, 'docs')
        self.artifact_dir = os.path.join(self.dir, 'artifacts')
        self.doc_dir = os.path.join(self.dir, 'docs/_build/html')
        write_cirrus_conf(self.config,
            **{
                'package': {'name': 'cirrus_unittest', 'version': '1.2.3'},
                'doc': {
                    'sphinx_makefile_dir': self.doc_dir,
                    'sphinx_doc_dir': self.doc_dir,
                    'artifact_dir': self.artifact_dir,
                    'file_server_upload_path': '/path/to/upload/dir'
                }
            }
        )
        self.harness = CirrusConfigurationHarness('cirrus.documentation_utils.load_configuration', self.config)
        self.harness.setUp()
        self.patch_local = mock.patch('cirrus.documentation_utils.local')
        self.mock_local = self.patch_local.start()
        self.doc_artifact_name = doc_artifact_name(self.harness.config)

    def tearDown(self):
        self.harness.tearDown()
        self.patch_local.stop()
        if os.path.exists(self.dir):
            os.system('rm -rf {0}'.format(self.dir))

    def test_build_docs(self):
        """test build_docs()"""
        os.getcwd = mock.Mock(return_value='')
        build_docs(make_opts=[])
        self.assertTrue(self.mock_local.called_once_with(
            '. ./venv/bin/activate && cd {} && make clean html'.format(self.makefile_dir)
        ))

        build_docs(make_opts=['man'])
        self.assertTrue(self.mock_local.called_once_with(
            '. ./venv/bin/activate && cd {} && make man'.format(self.makefile_dir)
        ))

    @mock.patch('cirrus.documentation_utils.os.path.exists')
    def test_build_doc_artifact(self, mock_exists):
        """test build_doc_artifact()"""
        mock_exists.return_value = True
        with mock.patch('cirrus.documentation_utils.tarfile.open') as mock_tar:
            self.assertTrue(mock_tar.add.called_once_with(
                self.doc_dir, arcname='cirrus_unittest-1.2.3', recursive=False)
            )

    @mock.patch('cirrus.documentation_utils.os.path.exists')
    def test_build_doc_artifact_raises(self, mock_exists):
        """should raise when doc dir is not present"""
        mock_exists.return_value = False
        self.assertRaises(RuntimeError, build_doc_artifact)


class TestUploadFileServer(unittest.TestCase):
    def setUp(self):
        """set up test files"""
        self.dir = tempfile.mkdtemp()
        self.config = os.path.join(self.dir, 'cirrus.conf')
        self.makefile_dir = os.path.join(self.dir, 'docs')
        self.artifact_dir = os.path.join(self.dir, 'artifacts')
        self.doc_dir = os.path.join(self.dir, 'docs/_build/html')
        write_cirrus_conf(self.config,
            **{
                'package': {'name': 'cirrus_unittest', 'version': '1.2.3'},
                'doc': {
                    'upload_method': 'file_server',
                    'sphinx_makefile_dir': self.doc_dir,
                    'sphinx_doc_dir': self.doc_dir,
                    'artifact_dir': self.artifact_dir,
                    'file_server_upload_path': '/path/to/upload/dir'
                }
            }
        )
        self.harness = CirrusConfigurationHarness('cirrus.documentation_utils.load_configuration', self.config)
        self.harness.setUp()
        self.doc_artifact_name = doc_artifact_name(self.harness.config)

    def tearDown(self):
        self.harness.tearDown()
        if os.path.exists(self.dir):
            os.system('rm -rf {0}'.format(self.dir))

    @mock.patch('cirrus.documentation_utils.get_plugin')
    @mock.patch('cirrus.documentation_utils.os.path.exists')
    def test_upload_documentation_file_server(self, mock_exists, mock_plugin):
        """test upload docs with file server"""
        plugin = mock.Mock()
        plugin.upload = mock.Mock()
        mock_exists.return_value = True
        mock_plugin.return_value = plugin
        opts = mock.Mock()
        opts.test = False
        upload_documentation(opts)
        self.assertTrue(plugin.upload.called)
        plugin.upload.assert_has_calls(
            [mock.call(opts, self.doc_artifact_name)]
        )


class TestUploadJenkins(unittest.TestCase):
    def setUp(self):
        """set up test files"""
        self.dir = tempfile.mkdtemp()
        self.config = os.path.join(self.dir, 'cirrus.conf')
        self.makefile_dir = os.path.join(self.dir, 'docs')
        self.artifact_dir = os.path.join(self.dir, 'artifacts')
        self.doc_dir = os.path.join(self.dir, 'docs/_build/html')
        write_cirrus_conf(self.config,
            **{
                'package': {'name': 'cirrus_unittest', 'version': '1.2.3'},
                'doc': {
                    'upload_method': 'jenkins',
                    'sphinx_makefile_dir': self.doc_dir,
                    'sphinx_doc_dir': self.doc_dir,
                    'artifact_dir': self.artifact_dir,
                    'file_server_upload_path': '/path/to/upload/dir'
                },
                'jenkins': {
                    'url': 'http://localhost:8080',
                    'doc_job': 'default',
                    'doc_var': 'archive',
                    'arc_var': 'ARCNAME'
                }
            }
        )
        self.harness = CirrusConfigurationHarness('cirrus.documentation_utils.load_configuration', self.config)
        self.harness.setUp()
        self.patch_local = mock.patch('cirrus.documentation_utils.local')
        self.mock_local = self.patch_local.start()
        self.doc_artifact_name = doc_artifact_name(self.harness.config)

    def tearDown(self):
        self.harness.tearDown()
        self.patch_local.stop()
        if os.path.exists(self.dir):
            os.system('rm -rf {0}'.format(self.dir))

    @mock.patch('cirrus.documentation_utils.os.path.exists')
    @mock.patch('cirrus.plugins.jenkins.requests.Session.post')
    @mock.patch('cirrus.plugins.jenkins.get_buildserver_auth')
    @mock.patch('cirrus.documentation_utils.MultipartEncoder')
    def test_upload_documentation_jenkins(self, MockEncoder, mock_auth, mock_post, mock_exists):
        """test upload docs with Jenkins"""
        mock_exists.return_value = True
        opts = mock.Mock()
        opts.test = False
        opts.docs = []
        mock_auth.return_value = 'someuser', 'abcdefghij'
        mock_resp = mock.Mock()
        mock_resp.status_code = 201
        mock_post.return_value = mock_resp

        with mock.patch('__builtin__.open', new_callable=mock.mock_open()):
            mock_encoder = mock.Mock()
            MockEncoder.return_value = mock_encoder

            upload_documentation(opts)

            self.assertEqual(mock_post.call_count, 1)

if __name__ == '__main__':
    unittest.main()
