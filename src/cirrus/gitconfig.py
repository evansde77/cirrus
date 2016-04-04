#!/usr/bin/env python
"""
gitconfig

local gitconfig parser/updater since the lib on pypi seems to be busted

"""
import os
import operator
import subprocess
import contextlib


@contextlib.contextmanager
def gitconfig(filename="~/.gitconfig"):
    c = GitConfig(filename)
    c.parse()
    yield c


def load_gitconfig(filename="~/.gitconfig"):
    c = GitConfig(filename)
    c.parse()
    return c


def shell_command(command):
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True
    )
    stdout, _ = process.communicate()
    if process.returncode != 0:
        raise RuntimeError(stdout)
    else:
        return "\n".join(stdout.splitlines())


class GitConfigSection(object):
    """
    helper/wrapper for a section of the gitconfig
    provides a basic dictionary like API
    """
    def __init__(self, config, section):
        self.section = section
        self.config = config

    def keys(self):
        """list parameter keys in section"""
        return dict(self.config)[self.section].keys()

    def values(self):
        """return all values in section"""
        return dict(self.config)[self.section].values()

    def items(self):
        """return key, value tuples of items in section"""
        return dict(self.config)[self.section].items()

    def get(self, key, default=None):
        return dict(self.config)[self.section].get(key, default)

    def __getitem__(self, key):
        return self.config.get_param(self.section, key)

    def __setitem__(self, key, value):
        self.config.set_param(self.section, key, value)

    def __delitem__(self, key):
        self.config.unset_param(self.section, key)

    def __str__(self):
        result = [
            "{0}.{1}={2}".format(self.section, k, v)
            for k, v in self.items()
        ]
        return '\n'.join(result)


class GitConfig(dict):
    """
    Object to encapsulate/parse/update a gitconfig file
    """
    def __init__(self, filename=None):
        super(GitConfig, self).__init__(self)
        if filename is None:
            filename = '${HOME}/.gitconfig'
        self.filename = os.path.expanduser(filename)

    @property
    def command(self):
        """base git config command"""
        return 'git config --file {0}'.format(self.filename)

    def parse(self):
        """re-read and parse all elements of git config and populate self"""
        self.clear()
        result = shell_command(self.command + " -l")
        for line in result.split('\n'):
            section, param_val = line.split('.', 1)
            sect_dict = self.setdefault(section, {})
            param, value = param_val.split('=', 1)
            sect_dict[param] = value

    @property
    def sections(self):
        """list sections in the gitconfig"""
        return self.keys()

    def __getitem__(self, key):
        """override getitem operator to wrap section in GitConfigSection"""
        if key in self:
            return GitConfigSection(self, key)
        raise KeyError(key)

    def get_param(self, section, param, default=None):
        """get a parameter from a section"""
        return self[section].get(param, default)

    def has_param(self, section, param, validator=lambda x: x is not None):
        """check parameter is present in section with optional validator"""
        if param not in section:
            return False
        return validator(self[section][param])

    def add_section(self, section):
        """add a new section, returns section instance"""
        self.set_param(section, 'cirrus-section-init-xyz', 'xyz')
        self.parse()
        return self[section]

    def set_param(self, section, param, value):
        """set/add parameter in section"""
        shell_command(self.command + ' {0}.{1} \"{2}\"'.format(section, param, str(value)))
        self.parse()

    def unset_param(self, section, param):
        """unset a parameter in the section provided"""
        shell_command(self.command + " --unset {0}.{1}".format(section, param))
        self.parse()

    @property
    def exists(self):
        """True if file exists"""
        return os.path.exists(self.filename)
