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

    def set_github_credentials(self, user, token):
        raise NotImplementedError(
            "{}.set_github_credentials".format(type(self).__name__)
        )

    def pypi_credentials(self):
        return {
            'username': None,
            'token': None,
        }

    def set_pypi_credentials(self, user, token):
        raise NotImplementedError(
            "{}.set_pypi_credentials".format(type(self).__name__)
        )

    def ssh_credentials(self):
        return {
            'ssh_username': None,
            'ssh_key': None
        }

    def set_ssh_credentials(self, user, keyfile):
        raise NotImplementedError(
            "{}.set_ssh_credentials".format(type(self).__name__)
        )

    def buildserver_credentials(self):
        return {
            'buildserver-user': None,
            'buildserver-token': None
        }

    def set_buildserver_credentials(self, user, token):
        raise NotImplementedError(
            "{}.set_buildserver_credentials".format(type(self).__name__)
        )

    def chef_credentials(self):
        return {
            'chef_server': None,
            'chef_username': None,
            'chef_keyfile': None,
            'chef_client_user': None,
            'chef_client_keyfile': None,
        }

    def set_chef_credentials(self, server, username, keyfile, client_user=None, client_key=None):
        raise NotImplementedError(
            "{}.set_chef_credentials".format(type(self).__name__)
        )

    def dockerhub_credentials(self):
        return {
            'username': None,
            'email': None,
            'password': None
        }

    def set_dockerhub_credentials(self, email, user, password):
        raise NotImplementedError(
            "{}.set_dockerhub_credentials".format(type(self).__name__)
        )

    def file_server_credentials(self):
        return {
            'file_server_username': None,
            'file_server_keyfile': None
        }

    def set_file_server_credentials(self, username, keyfile):
        raise NotImplementedError(
            "{}.set_file_server_credentials".format(type(self).__name__)
        )

    def credential_methods(self):
        """
        helper to grab all the *_credentials methods on this class
        """
        def match(x):
            result = (
                inspect.ismethod(x) and
                x.__name__.endswith('_credentials') and
                not x.__name__.startswith('set')
            )
            return result
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

if __name__ == '__main__':
    p = CredsPlugin()
    print p.credential_map()
