#!/usr/bin/env python
"""
test coverage for pypirc module
"""
import os
import tempfile
import unittest

from cirrus.pypirc import PypircFile

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


if __name__ == '__main__':
    unittest.main()
