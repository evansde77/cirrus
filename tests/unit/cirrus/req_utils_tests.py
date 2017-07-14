#!/usr/bin/env python

import os
import unittest
import tempfile
from cirrus.req_utils import ReqFile, bump_package


FIXTURE = \
"""
argparse
arrow==0.4.2
invoke
GitPython>=0.3.5
mock==1.0.1
nose===1.3.0
pep8==1.5.7
pylint<1.3.0
requests==2.3.0
PyChef==0.2.3
keyring>=8.5.1,<9.0.0
virtualenv
pluggage

dockerstache>=0.0.10
requests-toolbelt==0.6.2
tox
"""


class ReqFileTests(unittest.TestCase):
    """tests for req file operations"""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.file = os.path.join(self.dir, 'requirements.txt')
        with open(self.file, 'w') as handle:
            handle.write(FIXTURE)

    def tearDown(self):
        if os.path.exists(self.dir):
            os.system('rm -rf {}'.format(self.dir))

    def test_parsing_file(self):
        """read fixture, test methods"""
        rf = ReqFile(self.file)
        rf.parse()
        self.assertTrue(rf.has_package('argparse'))
        self.assertTrue(not rf.has_package('womp'))
        self.assertTrue(rf.package_has_version("requests"))
        self.assertTrue(not rf.package_has_version("invoke"))

    def test_bump(self):
        rf = ReqFile(self.file)
        rf.parse()
        rf.bump('argparse', '1.2.3')
        self.assertEqual(rf['argparse'], '1.2.3')
        rf.bump('arrow', '9.9.9')
        self.assertEqual(rf['arrow'], '9.9.9')

    def test_bump_package(self):
        bump_package(self.file, 'argparse', '8.9.7')
        rf = ReqFile(self.file)
        rf.parse()
        self.assertEqual(rf['argparse'], '8.9.7')

if __name__ == '__main__':
    unittest.main()
