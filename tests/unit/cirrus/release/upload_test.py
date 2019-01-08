import unittest
import mock


from cirrus.release.upload import upload_release


class UploadTests(unittest.TestCase):

    def setUp(self):

        self.patch_config = mock.patch('cirrus.release.upload.load_configuration')
        self.mock_load_conf = self.patch_config.start()
        self.mock_conf = mock.Mock()
        self.mock_load_conf.return_value = self.mock_conf
        self.mock_conf.package_name = mock.Mock(return_value='PACKAGE')
        self.mock_conf.package_version = mock.Mock(return_value='1.2.3')
        self.patch_plugin = mock.patch('cirrus.release.upload.get_plugin')
        self.mock_get_plugin = self.patch_plugin.start()
        self.mock_plugin = mock.Mock()
        self.mock_plugin.upload = mock.Mock()
        self.mock_get_plugin.return_value = self.mock_plugin

    def tearDown(self):
        self.patch_config.stop()
        self.patch_plugin.stop()

    def test_upload_release(self):
        mock_opts = mock.Mock()
        mock_opts.plugin = "PLUGIN"
        mock_opts.test = False
        with mock.patch("cirrus.release.upload.os.path.exists") as mock_exists:
            mock_exists(return_value=True)
            upload_release(mock_opts)
            self.assertTrue(self.mock_get_plugin.called)
            self.assertTrue(self.mock_plugin.upload.called)

    def test_upload_no_artifact(self):
        mock_opts = mock.Mock()
        mock_opts.plugin = "PLUGIN"
        mock_opts.test = False
        with mock.patch("cirrus.release.upload.os.path.exists") as mock_exists:
            mock_exists(return_value=False)
            self.assertRaises(RuntimeError, upload_release, mock_opts)


if __name__ == '__main__':
    unittest.main()