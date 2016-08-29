'''
qc command tests
'''
import mock
import unittest

from cirrus.quality_control import run_pep8
from cirrus.quality_control import run_pyflakes
from cirrus.quality_control import run_pylint
from cirrus.quality_control import main


def linter_side_effect(result):
    """
    Helper function to create a mock side-effect for
    one of the linter functions (i.e. pep8_file, etc...)
    the function retured takes a list of filenames
    and keyword parameters, and returns a tuple
    with the filename list and fake result as given.
    """
    def side_effect(filenames, **kwargs):
        return filenames, result
    return side_effect


class QualityControlTest(unittest.TestCase):

    def setUp(self):
        """setup mocks"""
        self.patch_config_load = mock.patch(
            'cirrus.quality_control.load_configuration')
        self.mock_config = self.patch_config_load.start()

        self.patch_pep8 = mock.patch('cirrus.quality_control.pep8_file')
        self.mock_pep8 = self.patch_pep8.start()
        self.patch_pyflakes = mock.patch('cirrus.quality_control.pyflakes_file')
        self.mock_pyflakes = self.patch_pyflakes.start()
        self.patch_pylint = mock.patch('cirrus.quality_control.pylint_file')
        self.mock_pylint = self.patch_pylint.start()

        self.patch_config = mock.patch('cirrus.quality_control.load_configuration')
        self.mock_config_get = self.patch_config.start()
        self.mock_config = mock.Mock()
        self.mock_config.package_name.return_value = 'testpackage'
        self.mock_config.quality_rcfile.return_value = 'rc_cola'
        self.mock_config.quality_threshold.return_value = 9.0
        self.mock_config_get.return_value = self.mock_config

        self.patch_sys = mock.patch('cirrus.quality_control.sys')
        self.mock_sys = self.patch_sys.start()

        self.patch_get_diff = mock.patch('cirrus.quality_control.get_diff_files')
        self.mock_diff_files = self.patch_get_diff.start()
        self.mock_diff_files.return_value = ['bar.ini', 'baz.yml', 'foo.py']

    def tearDown(self):
        self.patch_config_load.stop()
        self.patch_pep8.stop()
        self.patch_pyflakes.stop()
        self.patch_pylint.stop()
        self.patch_config.stop()
        self.patch_sys.stop()
        self.patch_get_diff.stop()

    def test_run_pylint_failure(self):
        self.mock_pylint.side_effect = linter_side_effect(3.42)
        result = run_pylint()
        self.mock_pylint.assert_called_once_with(
            ['testpackage'],
            rcfile='rc_cola'
        )
        self.assertFalse(result)

    def test_run_pylint_success(self):
        self.mock_pylint.side_effect = linter_side_effect(10.0)
        result = run_pylint()
        self.mock_pylint.assert_called_once_with(
            ['testpackage'],
            rcfile='rc_cola'
        )
        self.assertTrue(result)

    def test_run_pylint_files(self):
        self.mock_pylint.side_effect = linter_side_effect(10.0)
        result = run_pylint(files=['foo', 'bar'])
        self.mock_pylint.assert_called_once_with(
            ['foo', 'bar'],
            rcfile='rc_cola'
        )
        self.assertTrue(result)

    def test_run_pyflakes_failure(self):
        self.mock_pyflakes.side_effect = linter_side_effect(3)
        result = run_pyflakes(False)
        self.mock_pyflakes.assert_called_once_with(['testpackage'], verbose=False)
        self.assertFalse(result)

    def test_run_pyflakes_success(self):
        self.mock_pyflakes.side_effect = linter_side_effect(0)
        result = run_pyflakes(False)
        self.mock_pyflakes.assert_called_once_with(['testpackage'], verbose=False)
        self.assertTrue(result)

    def test_run_pyflakes_files_verbose(self):
        self.mock_pyflakes.side_effect = linter_side_effect(0)
        result = run_pyflakes(True, files=['foo', 'bar'])
        self.mock_pyflakes.assert_called_once_with(['foo', 'bar'], verbose=True)
        self.assertTrue(result)

    def test_run_pep8_failure(self):
        self.mock_pep8.side_effect = linter_side_effect(3)
        result = run_pep8(False)
        self.mock_pep8.assert_called_once_with(['testpackage'], verbose=False)
        self.assertFalse(result)

    def test_run_pep8_success(self):
        self.mock_pep8.side_effect = linter_side_effect(0)
        result = run_pep8(False)
        self.mock_pep8.assert_called_once_with(['testpackage'], verbose=False)
        self.assertTrue(result)

    def test_run_pep8_files_verbose(self):
        self.mock_pep8.side_effect = linter_side_effect(0)
        result = run_pep8(True, files=['foo', 'bar'])
        self.mock_pep8.assert_called_once_with(['foo', 'bar'], verbose=True)
        self.assertTrue(result)

    def test_qc_command_success(self):
        self.mock_pep8.side_effect = linter_side_effect(0)
        self.mock_pyflakes.side_effect = linter_side_effect(0)
        self.mock_pylint.side_effect = linter_side_effect(10.0)
        self.mock_sys.argv = ['qc']

        main()

        self.mock_pep8.assert_called_once_with(['testpackage'], verbose=False)
        self.mock_pyflakes.assert_called_once_with(['testpackage'], verbose=False)
        self.mock_pylint.assert_called_once_with(['testpackage'], rcfile='rc_cola')

    def test_qc_command_single_failure(self):
        self.mock_pep8.side_effect = linter_side_effect(0)
        self.mock_pyflakes.side_effect = linter_side_effect(3)
        self.mock_pylint.side_effect = linter_side_effect(10.0)
        self.mock_sys.argv = ['qc']

        main()

        self.mock_sys.exit.assert_called_once_with(1)
        self.mock_pep8.assert_called_once_with(['testpackage'], verbose=False)
        self.mock_pyflakes.assert_called_once_with(['testpackage'], verbose=False)
        self.mock_pylint.assert_called_once_with(['testpackage'], rcfile='rc_cola')

    def test_qc_command_multiple_failure(self):
        self.mock_pep8.side_effect = linter_side_effect(2)
        self.mock_pyflakes.side_effect = linter_side_effect(3)
        self.mock_pylint.side_effect = linter_side_effect(3.4)
        self.mock_sys.argv = ['qc']

        main()

        self.mock_sys.exit.assert_called_once_with(1)
        self.mock_pep8.assert_called_once_with(['testpackage'], verbose=False)
        self.mock_pyflakes.assert_called_once_with(['testpackage'], verbose=False)
        self.mock_pylint.assert_called_once_with(['testpackage'], rcfile='rc_cola')

    def test_qc_command_only_changes(self):
        self.mock_pep8.side_effect = linter_side_effect(2)
        self.mock_pyflakes.side_effect = linter_side_effect(3)
        self.mock_pylint.side_effect = linter_side_effect(3.4)
        self.mock_sys.argv = ['qc', '--only-changes']

        main()

        self.mock_sys.exit.assert_called_once_with(1)
        self.mock_pep8.assert_called_once_with(['foo.py'], verbose=False)
        self.mock_pyflakes.assert_called_once_with(['foo.py'], verbose=False)
        self.mock_pylint.assert_called_once_with(['foo.py'], rcfile='rc_cola')

    def test_qc_command_files(self):
        self.mock_pep8.side_effect = linter_side_effect(2)
        self.mock_pyflakes.side_effect = linter_side_effect(3)
        self.mock_pylint.side_effect = linter_side_effect(3.4)
        self.mock_sys.argv = ['qc', '-f', 'baz.py']

        main()

        self.mock_sys.exit.assert_called_once_with(1)
        self.mock_pep8.assert_called_once_with(['baz.py'], verbose=False)
        self.mock_pyflakes.assert_called_once_with(['baz.py'], verbose=False)
        self.mock_pylint.assert_called_once_with(['baz.py'], rcfile='rc_cola')

    def test_qc_command_changes_and_files_error(self):
        self.mock_sys.argv = ['qc', '-f', 'baz.py', '--only-changes']

        with self.assertRaises(ValueError):
            main()

        self.assertFalse(self.mock_pep8.called)
        self.assertFalse(self.mock_pyflakes.called)
        self.assertFalse(self.mock_pylint.called)


if __name__ == "__main__":
    unittest.main()
