#!/usr/bin/env python
"""
default

Default credential management that gets things from
your .gitconfig.

"""
import os
from cirrus.gitconfig import load_gitconfig
from cirrus.creds_plugin import CredsPlugin


class Default(CredsPlugin):
    """
    Default

    Get credentials from the users ~/.gitconfig file

    """
    PLUGGAGE_OBJECT_NAME = 'default'

    def __init__(self, gitconfig_file=None):
        self.gitconfig_file = gitconfig_file
        super(Default, self).__init__()

    def load(self):
        """
        load - override load hook to read the users .gitconfig file
        """
        if self.gitconfig_file is None:
            self.gitconfig_file = os.path.join(os.environ['HOME'], '.gitconfig')
        self.config = load_gitconfig(self.gitconfig_file)

    def github_credentials(self):
        github_user = self.config.get_param('cirrus', 'github-user')
        github_token = self.config.get_param('cirrus', 'github-token')
        return {
            'github_user': github_user,
            'github_token': github_token
        }

    def set_github_credentials(self, username, token):
        self.config.set_param('cirrus', 'github-user', username)
        self.config.set_param('cirrus', 'github-token', token)

    def pypi_credentials(self):
        pypi_user = self.config.get_param('cirrus', 'pypi-user')
        pypi_token = self.config.get_param('cirrus', 'pypi-token')
        return {
            'username': pypi_user,
            'token': pypi_token
        }

    def set_pypi_credentials(self, username, token):
        self.config.set_param('cirrus', 'pypi-user', username)
        self.config.set_param('cirrus', 'pypi-token', token)

    def ssh_credentials(self):
        pypi_ssh_user = self.config.get_param('cirrus', 'ssh-user')
        pypi_key = self.config.get_param('cirrus', 'ssh-key')
        return {
            'ssh_username': pypi_ssh_user,
            'ssh_key': pypi_key
        }

    def set_ssh_credentials(self, user, keyfile):
        self.config.set_param('cirrus', 'ssh-user', user)
        self.config.set_param('cirrus', 'ssh-key', keyfile)

    def buildserver_credentials(self):
        """

        """
        return {
            'buildserver-user': self.config.get_param('cirrus', 'buildserver-user'),
            'buildserver-token': self.config.get_param('cirrus', 'buildserver-token')
        }

    def set_buildserver_credentials(self, user, token):
        self.config.set_param('cirrus', 'buildserver-user', user)
        self.config.set_param('cirrus', 'buildserver-token', token)

    def chef_credentials(self):
        """

        """
        return {
            'chef_server': self.config.get_param('cirrus', 'chef-server'),
            'chef_username': self.config.get_param('cirrus', 'chef-username'),
            'chef_keyfile': self.config.get_param('cirrus', 'chef-keyfile'),
            'chef_client_user': self.config.get_param('cirrus', 'chef-client-user'),
            'chef_client_keyfile': self.config.get_param('cirrus', 'chef-client-keyfile')
        }

    def set_chef_credentials(self, server, username, keyfile, client_user=None, client_key=None):
        if client_user is None:
            client_user = username
        if client_key is None:
            client_key = keyfile

        self.config.set_param('cirrus', 'chef-server', server)
        self.config.set_param('cirrus', 'chef-username', username)
        self.config.set_param('cirrus', 'chef-keyfile', keyfile)
        self.config.set_param('cirrus', 'chef-client-user', client_user)
        self.config.set_param('cirrus', 'chef-client-keyfile', client_key)

    def dockerhub_credentials(self):
        return {
            'username': self.config.get_param('cirrus', 'docker-login-username'),
            'email': self.config.get_param('cirrus', 'docker-login-email'),
            'password': self.config.get_param('cirrus', 'docker-login-password')
        }

    def set_dockerhub_credentials(self, email, user, password):
        self.config.set_param('cirrus', 'docker-login-username', user)
        self.config.set_param('cirrus', 'docker-login-email', email)
        self.config.set_param('cirrus', 'docker-login-password', password)

    def file_server_credentials(self):
        return {
            'file_server_username': self.config.get_param('cirrus', 'file-server-username'),
            'file_server_keyfile': self.config.get_param('cirrus', 'file-server-keyfile')
        }

    def set_file_server_credentials(self, username, keyfile):
        self.config.set_param('cirrus', 'file-server-username', username)
        self.config.set_param('cirrus', 'file-server-keyfile', keyfile)
