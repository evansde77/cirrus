#!/usr/bin/env python
"""
unittests for cirrus.environment module

"""

import os
import copy
import unittest

from cirrus.environment import cirrus_home
from cirrus.environment import virtualenv_home

class EnvironmentFunctionTests(unittest.TestCase):
    """
    test case for environment module functions

    """
    def setUp(self):
        """save/mock the os.environ settings"""
        self.cirrus_home = copy.deepcopy(os.environ.get('CIRRUS_HOME'))
        self.venv_home =  copy.deepcopy(os.environ.get('VIRTUALENV_HOME'))


        os.environ['CIRRUS_HOME'] = "TESTVALUE"
        os.environ['VIRTUALENV_HOME'] = "TESTVALUE"

    def tearDown(self):
        """reset env vars"""
        if  self.cirrus_home is not None:
            os.environ['CIRRUS_HOME'] = self.cirrus_home
        if self.venv_home is not None:
            os.environ['VIRTUALENV_HOME'] = self.venv_home

    def test_cirrus_home(self):
        """test cirrus home function"""

        home1 = cirrus_home()
        self.assertEqual(home1, 'TESTVALUE')
        del os.environ['CIRRUS_HOME']

        home2 = cirrus_home()
        self.assertNotEqual(home2, 'TESTVALUE')

    def test_venv_home(self):
        """test venv home function"""
        home1 = virtualenv_home()
        self.assertEqual(home1, 'TESTVALUE')
        del os.environ['VIRTUALENV_HOME']

        home2 = virtualenv_home()
        self.assertEqual(home2, 'TESTVALUE/venv')


if __name__ == '__main__':
    unittest.main()


