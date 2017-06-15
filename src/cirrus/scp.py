#!/usr/bin/env python
"""
_scp_

SCP command wrapper to replace fabric put
with minimal dependencies

"""
from cirrus.invoke_helpers import local


class SCP(object):

    def __init__(self, **kwargs):
        self.target_host = kwargs['target_host']
        self.target_path = kwargs['target_path']
        self.source = kwargs['source']
        self.username = kwargs.get('ssh_username')
        self.ssh_key = kwargs.get('ssh_keyfile')
        self.ssh_config = kwargs.get('ssh_config')
        self.ssh_options = kwargs.get('ssh_options')
        self.scp_binary = kwargs.get('scp_binary', '/bin/scp')

    @property
    def scp_command(self):
        """build scp"""
        command = "{}".format(self.scp_binary)
        host_url = "{}:{}".format(self.target_host, self.target_path)
        if self.username:
            host_url = "{}@{}".format(self.username, host_url)
        opts = ""
        if self.ssh_config:
            opts += " -F {} ".format(self.ssh_config)
        if self.ssh_key:
            opts += " -i {} ".format(self.ssh_key)
        if self.ssh_options:
            opts += " {} ".format(self.ssh_options)
        return "{} {} {} {}".format(command, opts, self.source, host_url)

    def __call__(self):
        local(self.scp_command)


def put(local_file,
        target_file,
        target_host,
        ssh_username=None,
        ssh_keyfile=None,
        ssh_config=None,
        ssh_options=None,
        scp_binary=None
        ):
    """
    _put_

    Send a file to a remote host using scp under the hood.

    local_file: path to file to send
    target_file: path to put file on remote
    target_host: remote host

    Optional:
        ssh_username - username for remote system
        ssh_keyfile - ssh keyfile for auth
        ssh_config - ssh config file
        ssh_options - misc options for scp command
        scp_binary - scp binary (/bin/scp by default)

    """
    scp = SCP(
        source=local_file,
        target_path=target_file,
        target_host=target_host,
        ssh_username=ssh_username,
        ssh_keyfile=ssh_keyfile,
        ssh_config=ssh_config,
        ssh_options=ssh_options,
        scp_binary=scp_binary
    )
    scp()


