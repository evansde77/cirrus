#!/usr/bin/env python
"""
_fabric_helpers_

Utils/helpers for fabric api

"""
import copy
from fabric.api import env


class FabricHelper(object):
    """
    _FabricHelper_

    Context helper to set and clear fabric env
    to run a command on a given host

    Example usage;

    with FabricHelper('pypi.cloudant.com', 'evansde77', '/Users/david/.ssh/id_rsa'):
        run('/bin/date')

    Will run the date command on pypi.cloudant.com as evansde77 using the key file
    specified
    """
    def __init__(self, hostname, username, ssh_key):
        self.hostname = hostname
        self.username = username
        self.ssh_key = ssh_key
        # save settings
        self.hostname_cache = None
        self.username_cache = None
        self.ssh_key_cache = None

    def __enter__(self):
        self.hostname_cache = copy.copy(env.host_string)
        self.username_cache = copy.copy(env.user)
        self.ssh_key_cache = copy.copy(env.key_filename)

        env.host_string = self.hostname
        env.user = self.username
        env.key_filename = self.ssh_key
        return self

    def __exit__(self, *args):
        env.host_string = self.hostname_cache
        env.user = self.username_cache
        env.key_filename = self.ssh_key_cache



