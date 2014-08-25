'''
pylint_tools tests
'''
import mock
import unittest

from cirrus.pylint_tools import pep8_file
from cirrus.pylint_tools import pyflakes_file
from cirrus.pylint_tools import pylint_file


class Test(unittest.TestCase):

    def setUp(self):
        """setup mocks"""
        self.filename = 'hello.py'
        self.patch_local = mock.patch('cirrus.pylint_tools.local')
        self.patch_hide = mock.patch('cirrus.pylint_tools.hide')
        self.patch_settings = mock.patch('cirrus.pylint_tools.settings')

        self.mock_local = self.patch_local.start()
        self.mock_hide = self.patch_hide.start()
        self.mock_settings = self.patch_settings.start()

    def tearDown(self):
        """teardown mocks"""
        self.patch_local.stop()
        self.patch_hide.stop()
        self.patch_settings.stop()

    def test_pylint_file(self):
        """
        _test_pylint_file_
        """
        results = pylint_file(self.filename)
        self.failUnless(self.mock_local.called)
        self.failUnless(self.mock_hide.called)
        self.failUnless(self.mock_settings.called)
        self.failUnlessEqual(results[0], self.filename)

    def test_pyflakes_file(self):
        """
        _test_pyflakes_file_
        """
        results = pyflakes_file(self.filename)
        self.failUnless(self.mock_local.called)
        self.failUnless(self.mock_hide.called)
        self.failUnless(self.mock_settings.called)
        self.failUnlessEqual(results[0], self.filename)

    def pep8_file(self):
        """
        _test_pyflakes_file_
        """
        results = pep8_file(self.filename)
        self.failUnless(self.mock_local.called)
        self.failUnless(self.mock_hide.called)
        self.failUnless(self.mock_settings.called)
        self.failUnlessEqual(results[0], self.filename)

if __name__ == "__main__":
    unittest.main()
