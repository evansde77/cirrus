import unittest
import mock


import cirrus.release.utils as rutils
from cirrus.configuration import Configuration


class ReleaseUtilsTest(unittest.TestCase):
    """test cases for release utils"""

    def test_highlander(self):
        self.assertFalse(rutils.highlander([1,2,3]))
        self.assertTrue(rutils.highlander([True, False, False, False]))
        self.assertFalse(rutils.highlander([True, False, True, False]))
        self.assertFalse(rutils.highlander([False, False, False, False]))

    def test_parse_version(self):
        v = rutils.parse_version('1.2.3')
        self.assertEqual(v['major'], 1)
        self.assertEqual(v['minor'], 2)
        self.assertEqual(v['micro'], 3)

    def test_bump_version(self):
        bumped = rutils.bump_version_field('1.2.3')
        self.assertEqual(bumped, '2.0.0')
        bumped = rutils.bump_version_field('1.2.3', 'minor')
        self.assertEqual(bumped, '1.3.0')
        bumped = rutils.bump_version_field('1.2.3', 'micro')
        self.assertEqual(bumped, '1.2.4')

    @mock.patch('cirrus.release.utils.os.getcwd')
    def test_artifact_names(self, mock_cwd):
        mock_conf = mock.Mock()
        mock_conf.package_name = mock.Mock(return_value='PACKAGE')
        mock_conf.package_version = mock.Mock(return_value='1.2.3')
        mock_cwd.return_value = 'DIRNAME'

        an = rutils.artifact_name(mock_conf)
        self.assertEqual(an, 'DIRNAME/dist/PACKAGE-1.2.3.tar.gz')

        en = rutils.egg_artifact_name(mock_conf)
        wn = rutils.wheel_artifact_name(mock_conf)
        self.assertEqual(en, 'DIRNAME/dist/PACKAGE-1.2.3.tar.gz')
        self.assertEqual('DIRNAME/dist/PACKAGE-1.2.3.tar.gz', wn)

    def test_release_config(self):
        conf = Configuration(None)
        mock_opts = mock.Mock()
        mock_opts.wait_on_ci = False
        mock_opts.github_context_string = None
        mock_opts.github_develop_context_string = None
        mock_opts.github_master_context_string = None
        c = rutils.release_config(conf, mock_opts)
        expected = {'wait_on_ci': False,
            'wait_on_ci_develop': False,
            'wait_on_ci_master': False,
            'wait_on_ci_timeout': 600,
            'wait_on_ci_interval': 2,
            'push_retry_attempts': 1,
            'push_retry_cooloff': 0,
            'github_context_string': None,
            'update_github_context': False,
            'develop_github_context_string': None,
            'master_github_context_string': None,
            'update_develop_github_context': False,
            'update_master_github_context': False}
        for k, v in expected.items():
            self.assertTrue(k in c)
            self.assertEqual(c[k], v)

    @mock.patch('cirrus.release.utils.load_configuration')
    def test_is_nightly(self, mock_lc):
        mock_conf = mock.Mock()
        mock_conf.has_section = mock.Mock(return_value=False)
        mock_conf.package_version = mock.Mock(return_value='1.2.3')
        mock_conf.update_package_version = mock.Mock()
        mock_lc.return_value = mock_conf
        self.assertFalse(rutils.is_nightly('0.1.2'))
        self.assertTrue(rutils.is_nightly("1.2.3-nightly-20101010"))

        self.assertTrue(rutils.new_nightly().startswith('1.2.3-nightly-'))

        mock_conf.package_version = mock.Mock(return_value='1.2.3-nightly-20101010')
        mock_ghc = mock.Mock()
        rutils.remove_nightly(mock_ghc)
        self.assertTrue(mock_conf.update_package_version.called)
        mock_conf.update_package_version.assert_has_calls([mock.call('1.2.3')])


if __name__ == '__main__':
    unittest.main()