'''
qc command tests
'''
import mock
import unittest

from cirrus.quality_control import main, run_linters, build_parser


class QCCommandTests(unittest.TestCase):
    """
    test coverage for qc command module

    """
    def test_build_parser(self):
        """test build_parser call"""
        args = [
            '--include-files', 'file1', 'file2',
            '--exclude-files', 'file3', 'file4',
            '--exclude-dirs', 'dir1',
            '--linters', 'Pep8', 'Pyflakes'
        ]
        qc_conf = {}
        opts = build_parser(args, qc_conf)
        self.assertEqual(opts.include_files, ['file1', 'file2'])
        self.assertEqual(opts.exclude_files, ['file3', 'file4'])
        self.assertEqual(opts.exclude_dirs, ['dir1'])
        self.assertEqual(opts.linters, ['Pep8', 'Pyflakes'])

        qc_conf = {'exclude_dirs': ['dir3', 'dir4']}
        args = [
            '--include-files', 'file1', 'file2',
            '--exclude-files', 'file3', 'file4',
            '--linters', 'Pep8', 'Pyflakes'
        ]
        opts = build_parser(args, qc_conf)
        self.assertEqual(opts.exclude_dirs, ['dir3', 'dir4'])

    @mock.patch("cirrus.quality_control.load_configuration")
    @mock.patch("cirrus.quality_control.FACTORY")
    def test_run_linters(self, mock_factory, mock_conf):
        """test pass case"""
        mock_linter = mock.Mock()
        mock_linter.test_mode = False
        mock_linter.check = mock.Mock()
        mock_linter.errors = None
        mock_factory.return_value = mock_linter
        mock_factory.registry = {
            'Pep8': None,
            'Pylint': None
        }

        opts = mock.Mock()
        opts.test_only = False
        opts.linters = ['Pep8', 'Pylint']
        run_linters(opts, mock_conf, {})
        self.assertTrue(mock_linter.check.called)
        self.assertEqual(mock_linter.check.call_count, 2)

    @mock.patch("cirrus.quality_control.load_configuration")
    @mock.patch("cirrus.quality_control.FACTORY")
    def test_run_linters_fail(self, mock_factory, mock_conf):
        """test fail case"""
        mock_linter = mock.Mock()
        mock_linter.test_mode = False
        mock_linter.check = mock.Mock()
        mock_linter.errors = 100
        mock_factory.return_value = mock_linter
        mock_factory.registry = {
            'Pep8': None,
            'Pylint': None
        }

        opts = mock.Mock()
        opts.test_only = False
        opts.linters = ['Pep8', 'Pylint']
        self.assertRaises(RuntimeError, run_linters, opts, mock_conf, {})

    @mock.patch("cirrus.quality_control.load_configuration")
    @mock.patch("cirrus.quality_control.FACTORY")
    def test_bad_linter_name(self, mock_factory, mock_conf):
        """test fail case"""
        mock_linter = mock.Mock()
        mock_linter.test_mode = False
        mock_linter.check = mock.Mock()
        mock_linter.errors = 100
        mock_factory.return_value = mock_linter
        mock_factory.registry = {
            'Pep8': None,
            'Pylint': None
        }

        opts = mock.Mock()
        opts.test_only = False
        opts.linters = ['WOMP']
        self.assertRaises(RuntimeError, run_linters, opts, mock_conf, {})

    @mock.patch("cirrus.quality_control.load_configuration")
    @mock.patch("cirrus.quality_control.build_parser")
    @mock.patch("cirrus.quality_control.run_linters")
    @mock.patch("cirrus.quality_control.get_diff_files")
    def test_main(self, mock_diffs, mock_rl, mock_bp, mock_conf):
        mock_qc = {}
        mock_conf.quality_control = mock.Mock(return_value=mock_qc)
        mock_opts = mock.Mock()
        mock_opts.only_changes = False
        mock_bp.return_value = mock_opts

        main()
        self.assertTrue(mock_rl.called)

    @mock.patch("cirrus.quality_control.load_configuration")
    @mock.patch("cirrus.quality_control.build_parser")
    @mock.patch("cirrus.quality_control.run_linters")
    @mock.patch("cirrus.quality_control.get_diff_files")
    def test_main_diffs(self, mock_diffs, mock_rl, mock_bp, mock_conf):
        mock_qc = {}
        mock_conf.quality_control = mock.Mock(return_value=mock_qc)
        mock_opts = mock.Mock()
        mock_opts.only_changes = True
        mock_opts.incude_files = None
        mock_bp.return_value = mock_opts
        mock_diffs.return_value = ['DIFF1.py', 'DIFF2.py']

        main()
        self.assertTrue(mock_rl.called)
        self.assertEqual(mock_opts.include_files, mock_diffs.return_value)

        mock_diffs.return_value = []
        self.assertRaises(SystemExit, main)


if __name__ == '__main__':
    unittest.main()
