#!/usr/bin/env python
"""
test coverage for pypirc module
"""
import os
import mock
import tempfile
import unittest

from cirrus.pypirc import PypircFile, build_pip_command

PYPIRC = \
"""
[distutils]
index-servers =
  pypi
  devpi

[pypi]
repository: https://pypi.python.org/pypi/
username: steve
password: stevespass

[devpi]
repository: https://localhost:4000
username: the_steve
password: stevespass

"""


class PypircFileTest(unittest.TestCase):
    """test coverage for PypircFile class"""
    def setUp(self):
        """make a test pypirc file"""
        self.dir = tempfile.mkdtemp()
        self.file = os.path.join(self.dir, '.pypirc')
        with open(self.file, 'w') as handle:
            handle.write(PYPIRC)

    def tearDown(self):
        if os.path.exists(self.dir):
            os.system('rm -rf {}'.format(self.dir))

    def test_pypircfile(self):
        """test loading file and accessing data"""

        pypirc = PypircFile(self.file)
        self.failUnless(pypirc.exists())

        self.failUnless('pypi' in pypirc.index_servers)
        self.failUnless('devpi' in pypirc.index_servers)

        self.assertEqual(
            pypirc.get_pypi_url('pypi'),
            "https://steve:stevespass@https://pypi.python.org/pypi//simple"
        )
        self.assertEqual(
            pypirc.get_pypi_url('devpi'),
            "https://the_steve:stevespass@https://localhost:4000/simple"
        )

    def test_pypircfile_uses_default_filename_when_passed_none(self):
        pypirc = PypircFile(filename=None)
        self.assertTrue(pypirc.config_file.endswith('.pypirc'))

    def test_bad_pypi_name(self):
        pypirc = PypircFile(self.file)
        self.assertRaises(RuntimeError, pypirc.get_pypi_url, 'WOMP')

    def test_pip_command(self):
        config = mock.Mock()
        config.pypi_url = mock.Mock(return_value=None)
        config.pip_options = mock.Mock(return_value=' --pip-options ')

        pip = build_pip_command(config, 'PATH', 'requirements.txt', pypirc=self.file)
        self.assertEqual(pip.strip(), 'PATH/bin/pip install -r requirements.txt  --pip-options')

        config.pypi_url = mock.Mock(return_value='devpi')
        config.pip_options = mock.Mock(return_value=None)
        pip = build_pip_command(config, 'PATH', 'requirements.txt', pypirc=self.file)
        self.assertEqual(pip, 'PATH/bin/pip install -i https://the_steve:stevespass@https://localhost:4000/simple -r requirements.txt')

        pip = build_pip_command(config, 'PATH', 'requirements.txt', upgrade=True, pypirc=self.file)
        self.assertEqual(pip, 'PATH/bin/pip install -i https://the_steve:stevespass@https://localhost:4000/simple --upgrade -r requirements.txt')


if __name__ == '__main__':
    unittest.main()
