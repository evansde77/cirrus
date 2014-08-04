'''
Created on Aug 4, 2014

@author: jordancounts
'''
import git
import mox
import os
import posixpath
import tempfile
import unittest

import cirrus
from cirrus.git_tools import checkout_and_pull
# from tests.test_harness import GitTestHarness


class GitToolsTest(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.mox = mox.Mox()
        self.repo = self.mox.CreateMockAnything()
        self.mox.StubOutWithMock(
            cirrus.git_tools.git,
            'Repo',
            use_mock_anything=True)
        cirrus.git_tools.git.Repo(self.tempdir).AndReturn(self.repo)
        self.mox.StubOutWithMock(self.repo.heads, 'master')
        self.repo.heads.master().AndReturn(None)

    def tearDown(self):
        self.mox.UnsetStubs()
        os.rmdir(self.tempdir)

    def test_checkout_and_pull(self):
        self.mox.ReplayAll()
        checkout_and_pull(self.tempdir, 'master')
        self.mox.VerifyAll()


if __name__ == "__main__":
    unittest.main()
