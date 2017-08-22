#!/usr/bin/env python
"""
test coverage for builder plugin
"""
import unittest
import mock

from cirrus.builder_plugin import Builder


class BuilderPluginTest(unittest.TestCase):
    """tests for base builder plugin"""
    @mock.patch('cirrus.builder_plugin.load_configuration')
    @mock.patch('cirrus.builder_plugin.repo_directory')
    @mock.patch('cirrus.builder_plugin.local')
    def test_plugin(self, mock_local, mock_repo_dir, mock_load_conf):
        """test the basic plugin calls"""
        mock_conf = mock.Mock()
        mock_conf.get = mock.Mock(return_value={
            'build': {'builder': 'conf'},
            'extra_requirements': ['test-requirements.txt', 'more-reqs.txt']
        })
        mock_load_conf.return_value = mock_conf
        mock_repo_dir.return_value = "REPO"
        plug = Builder()
        plug.clean()
        plug.create()
        plug.activate()
        self.assertEqual(plug.venv_path, 'REPO/venv')
        self.assertEqual(plug.extra_reqs, ['test-requirements.txt', 'more-reqs.txt'])

        plug.run_setup_develop()
        self.assertTrue(mock_local.called)
        mock_local.assert_has_calls([
            mock.call('None && python setup.py develop')
        ])

        plug.plugin_parser.add_argument('-w', type=int)
        extras = plug.process_extra_args(['-w', '1', '-x', '2'])
        self.assertTrue('w' in extras)
        self.assertEqual(extras['w'], 1)
        self.assertEqual(plug.str_to_list('a,b,c'), ['a', 'b', 'c'])


if __name__ == '__main__':
    unittest.main()
