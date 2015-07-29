'''
qc command tests
'''
import mock
import unittest

from cirrus.quality_control import run_pep8
from cirrus.quality_control import run_pyflakes
from cirrus.quality_control import run_pylint


class QualityControlTest(unittest.TestCase):

    def setUp(self):
        """setup mocks"""
        self.patch_config_load = mock.patch(
            'cirrus.quality_control.load_configuration')
        self.mock_config = self.patch_config_load.start()

    def tearDown(self):
        self.patch_config_load.stop()

    def test_run_pylint(self):
        with mock.patch('cirrus.quality_control.pylint_file') as mock_pylint:
            run_pylint()
            self.failUnless(mock_pylint.called)

    def test_run_pyflakes(self):
        with mock.patch(
            'cirrus.quality_control.pyflakes_file') as mock_pyflakes:

            run_pyflakes(False)
            self.failUnless(mock_pyflakes.called)

    def test_run_pep8(self):
        with mock.patch('cirrus.quality_control.pep8_file') as mock_pep8:
            run_pep8(False)
            self.failUnless(mock_pep8.called)

if __name__ == "__main__":
    unittest.main()
