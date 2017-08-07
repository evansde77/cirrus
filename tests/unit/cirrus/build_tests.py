#!/usr/bin/env python
"""
build command test coverage
"""

import unittest
import mock

from cirrus.build import plugin_build, build_parser, get_builder_plugin


class BuildParserTests(unittest.TestCase):
    """test build_parser"""

    def test_build_parser(self):
        """test parser setup"""
        argv = ['build']
        opts, extras = build_parser(argv)
        self.assertEqual(opts.clean, False)
        self.assertEqual(opts.command, 'build')
        self.assertEqual(opts.docs, None)
        self.assertEqual(opts.extras, [])
        self.assertEqual(opts.nosetupdevelop, False)
        self.assertEqual(opts.upgrade, False)

        argv = ['build', '--no-setup-develop']
        opts, extras = build_parser(argv)
        self.failUnless(opts.nosetupdevelop)

        argv = [
            'build',
            '--extra-requirements',
            'test-requirements.txt',
            'other-requirements.txt'
        ]
        opts, extras = build_parser(argv)
        self.assertEqual(
            opts.extras,
            ['test-requirements.txt', 'other-requirements.txt']
        )


class PluginBuildTest(unittest.TestCase):
    """
    test callout to plugin
    """

    @mock.patch("cirrus.build.get_builder_plugin")
    @mock.patch("cirrus.build.FACTORY")
    def test_plugin_build(self, mock_factory,mock_get_plugin):
        mock_plugin = mock.Mock()
        mock_plugin.create = mock.Mock()
        mock_plugin.process_extra_args = mock.Mock(return_value=[])
        mock_get_plugin.return_value = "PLUGIN"
        mock_factory.return_value = mock_plugin
        mock_opts = mock.Mock()
        mock_opts.builder = None

        plugin_build(mock_opts, [('extra', 'args')])
        self.assertTrue(mock_plugin.create.called)
        self.assertTrue(mock_plugin.process_extra_args.called)

    @mock.patch('cirrus.build.load_configuration')
    @mock.patch('cirrus.build.is_anaconda')
    def test_get_builder_plugin(self, mock_ana, mock_conf):
        """test get plugin name method"""
        mock_config = mock.Mock()
        mock_config.get = mock.Mock(return_value={'builder': 'STEVE'})
        mock_config.has_gitconfig_param = mock.Mock(return_value=True)
        mock_config.get_gitconfig_param = mock.Mock(return_value='POOP')
        mock_conf.return_value = mock_config
        mock_ana.return_value = True
        self.assertEqual(get_builder_plugin(), 'POOP')
        mock_config.has_gitconfig_param.return_value = False
        self.assertEqual(get_builder_plugin(), 'STEVE')
        mock_config.get.return_value = {'builder': None}
        self.assertEqual(get_builder_plugin(), 'CondaPip')
        mock_ana.return_value = False
        self.assertEqual(get_builder_plugin(), 'VirtualenvPip')


if __name__ == '__main__':
    unittest.main()
