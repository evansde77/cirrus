#!/usr/bin/env python
"""
.pypirc file wrapper

"""
import os
import ConfigParser


class PypircFile(dict):
    """
    wrapper object for a pypirc file

    """
    def __init__(self, filename='~/.pypirc'):
        self.config_file = os.path.expanduser(filename)
        if self.exists():
            self.load()

    def exists(self):
        return os.path.exists(self.config_file)

    def load(self):
        """parse config file into self"""
        self.parser = ConfigParser.RawConfigParser()
        self.parser.read(self.config_file)
        for section in self.parser.sections():
            self.setdefault(section, {})
            for option in self.parser.options(section):
                self[section].setdefault(
                    option,
                    self.parser.get(section, option)
                )

    @property
    def index_servers(self):
        """get list of index servers defined in pypirc"""
        servers = self.get('distutils', {}).get('index-servers', '')
        return [s.strip() for s in servers.split('\n') if s.strip()]

    def get_pypi_url(self, index_alias):
        if index_alias not in self.index_servers:
            msg = "Unknown pypi index name: {}".format(index_alias)
            raise RuntimeError(msg)
        params = self[index_alias]
        url = (
            "https://{username}:{password}@{repository}/simple"
        ).format(**params)
        return url
