#!/usr/bin/env python
"""
.pypirc file wrapper

"""
import os
from cirrus._2to3 import ConfigParser, urlparse
from cirrus.configuration import get_pypi_auth


def build_pip_command(config, path, reqs_file, upgrade=False, pypirc=None):
    """
    given the package config, pypirc and various options,
    build the pip install command for a requirements file

    """
    pypi_server = config.pypi_url()
    pip_options = config.pip_options()
    pip_command_base = None
    if pypi_server is not None:
        pypirc = PypircFile(pypirc)
        if pypi_server in pypirc.index_servers:
            pypi_url = pypirc.get_pypi_url(pypi_server)
        else:
            pypi_conf = get_pypi_auth()
            pypi_url = (
                "https://{pypi_username}:{pypi_token}@{pypi_server}/simple"
            ).format(
                pypi_token=pypi_conf['token'],
                pypi_username=pypi_conf['username'],
                pypi_server=pypi_server
            )

        pip_command_base = (
            '{0}/bin/pip install -i {1}'
        ).format(path, pypi_url)

        if upgrade:
            cmd = (
                '{0} --upgrade '
                '-r {1}'
            ).format(pip_command_base, reqs_file)
        else:
            cmd = (
                '{0} '
                '-r {1}'
            ).format(pip_command_base, reqs_file)

    else:
        pip_command_base = '{0}/bin/pip install'.format(path)
        # no pypi server
        if upgrade:
            cmd = '{0} --upgrade -r {1}'.format(pip_command_base, reqs_file)
        else:
            cmd = '{0} -r {1}'.format(pip_command_base, reqs_file)

    if pip_options:
        cmd += " {} ".format(pip_options)

    return cmd


class PypircFile(dict):
    """
    wrapper object for a pypirc file

    """
    def __init__(self, filename=None):
        if filename is None:
            filename = '~/.pypirc'
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

    def pip_options(self):
        """
        create pip options string using --extra-index-url and
        --trusted-host for each index server
        """
        result = ""
        hosts = set()
        for idx in self.index_servers:
            repo = self[idx].get('repository')
            if not repo:
                continue
            result += ' --extra-index-url={}'.format(repo)
            netloc = urlparse(repo).netloc
            if ':' in netloc:
                netloc = netloc.split(':', 1)[0]
            hosts.add(netloc)

        for host in hosts:
            if host == 'localhost':
                continue
            result += ' --trusted-host={}'.format(host)
        return result
