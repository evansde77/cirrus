'''
pylint_tools tests
'''
import mock
import unittest

from cirrus.pylint_tools import pep8_file
from cirrus.pylint_tools import pyflakes_file
from cirrus.pylint_tools import pylint_file


class PylintToolsTest(unittest.TestCase):

    def setUp(self):
        """setup mocks"""
        self.filename = 'hello.py'
        self.patch_local = mock.patch('cirrus.pylint_tools.local')

        self.mock_local = self.patch_local.start()

    def tearDown(self):
        """teardown mocks"""
        self.patch_local.stop()

    def test_pylint_file(self):
        """
        _test_pylint_file_
        """
        results = pylint_file(self.filename)
        self.failUnless(self.mock_local.called)
        self.failUnlessEqual(results[0], self.filename)

    def test_pyflakes_file(self):
        """
        _test_pyflakes_file_
        """
        results = pyflakes_file(self.filename)
        self.failUnless(self.mock_local.called)
        self.failUnlessEqual(results[0], self.filename)

    def pep8_file(self):
        """
        _test_pyflakes_file_
        """
        results = pep8_file(self.filename)
        self.failUnless(self.mock_local.called)
        self.failUnlessEqual(results[0], self.filename)

if __name__ == "__main__":
    unittest.main()
