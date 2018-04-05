#!/usr/bin/env python
"""
package_container_tests

"""

import os
import mock
import tempfile
import unittest

from cirrus.utils import working_dir
from cirrus.package_container import init_container


class InitContainerTests(unittest.TestCase):
    """
    tests for init_container method
    """
    def setUp(self):
        """set up fake package"""
        self.dir = tempfile.mkdtemp()
        self.cirrus_conf = os.path.join(self.dir, 'cirrus.conf')
        self.gitconf_str = "cirrus.credential-plugin=default"
        with open(self.cirrus_conf, 'w') as handle:
            handle.write("[package]\n")
            handle.write("name=steves_package\n")
            handle.write("version=0.0.0\n")
            handle.write("author_email=steve@pbr.com\n")
            handle.write("[pypi]\n")
            handle.write("pip_options=PIP_OPTS\n")

        self.patch_environ = mock.patch.dict(
            os.environ,
            {
                'HOME': self.dir,
                'USER': 'steve',
            }
        )
        self.patch_environ.start()
        self.patch_gitconfig = mock.patch('cirrus.gitconfig.shell_command')
        self.mock_gitconfig = self.patch_gitconfig.start()
        self.mock_gitconfig.return_value = self.gitconf_str
        self.patch_unstaged = mock.patch('cirrus.package_container.has_unstaged_changes')
        self.patch_checkout = mock.patch('cirrus.package_container.checkout_and_pull')
        self.patch_commit = mock.patch('cirrus.package_container.commit_files_optional_push')
        self.mock_unstaged = self.patch_unstaged.start()
        self.mock_unstaged.return_value = False
        self.mock_checkout = self.patch_checkout.start()
        self.mock_commit = self.patch_commit.start()

    def tearDown(self):
        """clean up"""
        self.patch_unstaged.stop()
        self.patch_checkout.stop()
        self.patch_gitconfig.stop()
        self.patch_commit.stop()
        self.patch_environ.stop()
        if os.path.exists(self.dir):
            os.system('rm -rf {}'.format(self.dir))

    def test_init_container(self):
        """test init_container call"""

        opts = mock.Mock()
        opts.repo = self.dir
        opts.template_dir = "container-template"
        opts.image_dir = "container-image"
        opts.container = "steve/awesome-image:latest"
        opts.entrypoint = "/bin/bash"
        opts.docker_registry = None
        opts.virtualenv = "/pyenvy/venvs/data_py2"
        with working_dir(self.dir):
            init_container(opts)

        templates = os.path.join(self.dir, 'container-template')
        expected_files = [
            '.dockerstache',
            'context.json',
            'Dockerfile.mustache',
            'post_script.sh',
            'pre_script.sh',
            'install_script.sh.mustache'
        ]
        self.failUnless(os.path.exists(templates))
        found = os.listdir(templates)
        for exp in expected_files:

            self.failUnless(exp in found)
        dockerfile = os.path.join(templates, 'Dockerfile.mustache')
        with open(dockerfile, 'r') as handle:
            content = handle.read()

        self.failUnless("FROM steve/awesome-image:latest" in content)
        self.failUnless("MAINTAINER steve@pbr.com" in content)
        self.failUnless("ENTRYPOINT [\"/bin/bash\"]" in content)

        with open(self.cirrus_conf, 'r') as handle:
            conf = handle.read()
        self.failUnless('[docker]' in conf)
        self.failUnless('dockerstache_template = container-template' in conf)
        self.failUnless('dockerstache_context = container-template/context.json' in conf)
        self.failUnless('directory = container-image' in conf)

        install_script = os.path.join(
            templates,
            'install_script.sh.mustache'
        )
        with open(install_script, 'r') as handle:
            local = handle.read()
            print(local)
            self.failUnless('. /pyenvy/venvs/data_py2/bin/activate' in local)
            self.failUnless('pip install PIP_OPTS' in local)

        pre_script = os.path.join(
            templates, "pre_script.sh"
        )
        with open(pre_script, 'r') as handle:
            script = handle.read()
            print(script)


if __name__ == '__main__':
    unittest.main()
