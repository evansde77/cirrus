#!/usr/bin/env python
"""
tests for gitconfig module
"""
import os
import tempfile
import unittest
from cirrus.gitconfig import load_gitconfig

CONFIG1 = \
"""
[alias]
    cirrus = ! /Users/devans/.cirrus/venv/bin/cirrus
    jira = ! /Users/devans/.jira-cli/venv/bin/jira
[push]
    default = matching
[pull]
    rebase = true
"""

CONFIG2 = \
"""
[alias]
    cirrus = ! /Users/devans/.cirrus/venv/bin/cirrus
    jira = ! /Users/devans/.jira-cli/venv/bin/jira
    hello = "!f() { \
            echo fetching...; \
        }; f"
[push]
    default = matching
[pull]
    rebase = true
"""


class GitConfigTests(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.file_1 = os.path.join(self.dir, 'gc1')
        self.file_2 = os.path.join(self.dir, 'gc2')

        with open(self.file_1, 'w') as handle:
            handle.write(CONFIG1)

        with open(self.file_2, 'w') as handle:
            handle.write(CONFIG2)

    def tearDown(self):
        if os.path.exists(self.dir):
            os.system('rm -rf {}'.format(self.dir))

    def test_reading_config1(self):
        gc = load_gitconfig(filename=self.file_1)
        self.assertTrue('push' in gc.sections)
        self.assertTrue('pull' in gc.sections)
        self.assertTrue('alias' in gc.sections)

    def test_reading_config2(self):
        gc = load_gitconfig(filename=self.file_2)
        self.assertTrue('push' in gc.sections)
        self.assertTrue('pull' in gc.sections)
        self.assertTrue('alias' in gc.sections)



if __name__ == '__main__':
    unittest.main()
