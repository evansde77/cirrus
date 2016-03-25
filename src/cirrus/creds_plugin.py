#!/usr/bin/env
"""
creds_plugin

"""
import inspect
from pluggage.factory_plugin import PluggagePlugin


class CredsPlugin(PluggagePlugin):
    """
    base class for a credential manager plugin.
    Subclasses should override the load and *_credentials
    methods to return the equivalent dictionary containing
    the required creds

    """
    PLUGGAGE_FACTORY_NAME = 'credentials'

    def __init__(self):
        super(CredsPlugin, self).__init__()
        self.load()

    def load(self):
        """override to do any loading steps needed"""
        pass

    def github_credentials(self):
        return {
            'github_user': None,
            'github_token': None
        }

    def pypi_credentials(self):
        return {
            'username': None,
            'token': None,
        }

    def ssh_credentials(self):
        return {
            'ssh_username': None,
            'ssh_key': None
        }

    def buildserver_credentials(self):
        return {
            'buildserver-user': None,
            'buildserver-token': None
        }

    def chef_credentials(self):
        return {
            'chef_server': None,
            'chef_username': None,
            'chef_keyfile': None,
            'chef_client_user': None,
            'chef_client_keyfile': None,
        }

    def dockerhub_credentials(self):
        return {
            'username': None,
            'email': None,
            'password': None
        }

    def credential_methods(self):
        """
        helper to grab all the *_credentials methods on this class
        """
        match = lambda x: inspect.ismethod(x) and x.__name__.endswith('_credentials')
        return [x for x in inspect.getmembers(self, predicate=match)]

    def credential_map(self):
        """
        produces a nested credential dictionary that can be used
        to render templates with a standard format for looking
        up a credential

        """
        result = {}
        for m_name, m_func in self.credential_methods():
            result[m_name] = m_func()
        return result
