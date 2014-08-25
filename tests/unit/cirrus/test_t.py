'''
test command tests
'''
import mock
import unittest

from cirrus.test import nose_test


class TestTest(unittest.TestCase):

    def test_nose_test(self):
        with mock.patch('cirrus.test.load_configuration') as mock_config:
            with mock.patch('cirrus.test.local') as mock_local:
                nose_test('default')
                self.failUnless(mock_config.called)
                self.failUnless(mock_local.called)


if __name__ == "__main__":
    unittest.main()