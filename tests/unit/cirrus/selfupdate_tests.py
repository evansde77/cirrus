#!/usr/bin/env python
"""
selfupdate unittests
"""

import unittest
import mock
import os
import tempfile

from cirrus.selfupdate import pip_update, latest_release


class SelfupdateTests(unittest.TestCase):


    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.patch_local = mock.patch('cirrus.selfupdate.local')
        self.mock_local = self.patch_local.start()
        self.patch_chdir = mock.patch('cirrus.selfupdate.chdir')
        self.mock_chdir = self.patch_chdir.start()

        self.mock_local = self.patch_local.start()
        self.patch_home = mock.patch('cirrus.selfupdate.cirrus_home')
        self.patch_venv = mock.patch('cirrus.selfupdate.virtualenv_home')
        self.mock_cirrus_home = self.patch_home.start()
        self.mock_cirrus_home.return_value = self.dir
        self.mock_venv = self.patch_venv.start()
        self.mock_venv.return_value = os.path.join(self.dir, 'venv')

    def tearDown(self):
        self.patch_home.stop()
        self.patch_local.stop()
        self.patch_venv.stop()
        self.patch_chdir.stop()
        if os.path.exists(self.dir):
            os.system('rm -rf {}'.format(self.dir))

    @mock.patch('cirrus.selfupdate.is_anaconda')
    def test_pip_update(self, mock_ana):
        """test pip update"""
        mock_ana.return_value=False
        opts = mock.Mock()
        opts.version = "0.2.3"
        opts.upgrade_setuptools = True
        pip_update(opts)

        self.failUnless(self.mock_local.called)
        self.mock_local.assert_has_calls([
            mock.call(' . ./venv/bin/activate && pip install --upgrade setuptools'),
            mock.call(' . ./venv/bin/activate && pip install --upgrade cirrus-cli==0.2.3')
        ])

    @mock.patch('cirrus.selfupdate.is_anaconda')
    def test_pip_update_no_st(self, mock_ana):
        """test pip update no setuptools"""
        mock_ana.return_value=False
        opts = mock.Mock()
        opts.version = "0.2.3"
        opts.upgrade_setuptools = False
        pip_update(opts)

        self.failUnless(self.mock_local.called)
        self.mock_local.assert_has_calls([
            mock.call(' . ./venv/bin/activate && pip install --upgrade cirrus-cli==0.2.3')
        ])

    @mock.patch('cirrus.selfupdate.is_anaconda')
    def test_conda_update(self, mock_ana):
        """test pip update"""
        mock_ana.return_value=True
        opts = mock.Mock()
        opts.version = "0.2.3"
        opts.upgrade_setuptools = True
        pip_update(opts)

        venv_path = "{}/venv".format(self.dir)
        venv_activate = "{}/bin/activate".format(venv_path)

        self.failUnless(self.mock_local.called)
        self.mock_local.assert_has_calls([
            mock.call('source {} {} && pip install --upgrade setuptools'.format(venv_activate, venv_path)),
            mock.call('source {} {} && pip install --upgrade cirrus-cli==0.2.3'.format(venv_activate, venv_path))
        ])

    @mock.patch('cirrus.selfupdate.is_anaconda')
    def test_conda_update_no_st(self, mock_ana):
        """test pip update"""
        mock_ana.return_value=True
        opts = mock.Mock()
        opts.version = "0.2.3"
        opts.upgrade_setuptools = False
        pip_update(opts)

        venv_path = "{}/venv".format(self.dir)
        venv_activate = "{}/bin/activate".format(venv_path)

        self.failUnless(self.mock_local.called)
        self.mock_local.assert_has_calls([
            mock.call('source {} {} && pip install --upgrade cirrus-cli==0.2.3'.format(venv_activate, venv_path))
        ])


    @mock.patch('cirrus.selfupdate.get_releases')
    def test_latest_release(self, mock_gr):
        conf = mock.Mock()
        conf.organisation_name = mock.Mock(return_value='evansde77')
        conf.package_name = mock.Mock(return_value='cirrus')
        mock_gr.return_value = [{'tag_name': 'TAG1', 'published_at': "2015-12-03T15:21:37Z"}, {'tag_name': 'TAG2', 'published_at': "2016-12-03T15:21:37Z"}]
        self.assertEqual(latest_release(conf), 'TAG1')

if __name__ == '__main__':
    unittest.main()

