#!/usr/bin/env python
"""
_configuration_

Util class to read and access the cirrus.conf file
that defines how the various commands operate.

Commands should access this by doing

from cirrus.configuration import load_configuration
conf = load_configuration()

"""
import os
from cirrus.gitconfig import load_gitconfig
from cirrus.environment import repo_directory
import subprocess
import ConfigParser
import pluggage.registry


def get_creds_plugin(plugin_name):
    """
    _get_creds_plugin_

    Get the credential access plugin requested from the factory
    """
    factory = pluggage.registry.get_factory(
        'credentials',
        load_modules=['cirrus.plugins.creds']
    )
    return factory(plugin_name)


class Configuration(dict):
    """
    _Configuration_

    """
    def __init__(self, config_file, gitconfig_file=None):
        super(Configuration, self).__init__(self)
        self.gitconfig_file = gitconfig_file
        self.config_file = config_file
        self.parser = None
        self.credentials = None
        self.gitconfig = None

    def load(self):
        """
        _load_from_file_

        Reread the cirrus config file

        """
        self.parser = ConfigParser.RawConfigParser()
        self.parser.read(self.config_file)
        for section in self.parser.sections():
            self.setdefault(section, {})
            for option in self.parser.options(section):
                self[section].setdefault(
                    option,
                    self.parser.get(section, option)
                )
        if self.gitconfig_file is None:
            self.gitconfig_file = os.path.join(os.environ['HOME'], '.gitconfig')
        self.gitconfig = load_gitconfig(self.gitconfig_file)
        self._load_creds_plugin()

    def setup_load(self):
        if self.gitconfig_file is None:
            self.gitconfig_file = os.path.join(os.environ['HOME'], '.gitconfig')
        self.gitconfig = load_gitconfig(self.gitconfig_file)
        self.gitconfig.add_section('cirrus')
        self._load_creds_plugin()

    def _load_creds_plugin(self):
        """look up plugin pref fron gitconfig and load cred plugin"""
        plugin_name = self.gitconfig.get_param('cirrus', 'credential-plugin')
        if not plugin_name:
            plugin_name = 'default'
        self.credentials = get_creds_plugin(plugin_name)

    def _set_creds_plugin(self, plugin):
        self.set_gitconfig_param('credential-plugin', plugin)
        self._load_creds_plugin()

    def set_gitconfig_param(self, param, value, section='cirrus'):
        """
        helper to set params in users .gitconfig
        """
        self.gitconfig.set_param(section, param, value)

    def get_gitconfig_param(self, param, section='cirrus'):
        """helper to read values from users .gitconfig"""
        return self.gitconfig.get_param(section, param)

    def has_gitconfig_param(
            self, param, section='cirrus', validator=lambda x: x is not None
            ):
        """helper to check if a gitconfig param is set/present"""
        if not param in self.list_gitconfig_params(section):
            return False
        return validator(self.gitconfig.get_param(section, param))

    def list_gitconfig_params(self, section='cirrus'):
        return self.gitconfig[section].keys()

    def has_section(self, section):
        return section in self

    def get_param(self, section, param, default=None):
        """
        _get_param_

        convienience param getter with section, param name and
        optional default to avoid key errors
        """
        if section not in self:
            raise KeyError('section {0} not found'.format(section))
        return self[section].get(param, default)

    def package_version(self):
        return self.get('package', {}).get('version')

    def package_name(self):
        return self.get('package', {}).get('name')

    def organisation_name(self):
        return self.get('package', {}).get('organization')

    def release_notes_format(self):
        return self.get('package', {}).get('release_notes_format', 'plaintext')

    def pypi_url(self):
        return self.get('pypi', {}).get('pypi_url')

    def pip_options(self):
        return self.get('pypi', {}).get('pip_options')

    def pypi_config(self):
        """
        get the details for uploading to pypi

        """
        return self.get('pypi', {})

    def gitflow_branch_name(self):
        return self.get('gitflow', {}).get('develop_branch', 'develop')

    def gitflow_master_name(self):
        return self.get('gitflow', {}).get('master_branch', 'master')

    def gitflow_feature_prefix(self):
        return self.get('gitflow', {}).get('feature_branch_prefix', 'feature/')

    def gitflow_release_prefix(self):
        return self.get('gitflow', {}).get('release_branch_prefix', 'release/')

    def test_where(self, suite):
        return self.get('test-{0}'.format(suite), {}).get('where')

    def test_mode(self, suite):
        return self.get('test-{0}'.format(suite), {}).get('mode')

    def venv_name(self):
        return self.get('build', {}).get('virtualenv_name', 'venv')

    def quality_rcfile(self):
        return self.get('quality', {}).get('rcfile')

    def quality_threshold(self):
        return float(self.get('quality', {}).get('threshold'))

    def release_notes(self):
        """
        returns the release notes file and release
        notes sentinel from the config
        """
        return (
            self.get('package', {}).get('release_notes_file'),
            self.get('package', {}).get('release_notes_sentinel')
        )

    def version_file(self):
        """
        returns the version file and version attr from the configuration
        """
        return (
            self.get('package', {}).get('version_file'),
            self.get('package', {}).get('version_attribute', '__version__')
        )

    def update_package_version(self, new_version):
        """
        _update_package_version_

        Update the version in the configuration field
        """
        self['package']['version'] = new_version
        self.parser.set('package', 'version', new_version)
        with open(self.config_file, 'w') as handle:
            self.parser.write(handle)

    def configuration_map(self):
        result = {
            "cirrus": {
                "configuration": dict(self),
                "credentials": self.credentials.credential_map()
            }
        }
        return result


def load_configuration(package_dir=None, gitconfig_file=None):
    """
    _load_configuration_

    Load the cirrus.conf file and parse it into a nested dictionary
    like Configuration instance.

    :param package_dir: Location of cirrus managed package if not pwd
    :param gitconfig_file: Path to gitconfig if not ~/.gitconfig
    :returns: Configuration instance

    """
    dirname = os.getcwd()
    if package_dir is not None:
        dirname = package_dir

    config_path = os.path.join(dirname, 'cirrus.conf')
    if not os.path.exists(config_path):
        repo_dir = repo_directory()
        if repo_dir is not None:
            config_path = os.path.join(repo_dir, 'cirrus.conf')

    if not os.path.exists(config_path):
        msg = "Couldnt find ./cirrus.conf, are you in a package directory?"
        raise RuntimeError(msg)

    config_instance = Configuration(config_path, gitconfig_file=gitconfig_file)
    config_instance.load()
    return config_instance


def load_setup_configuration(package_dir=None, gitconfig_file=None):
    """
    _load_setup_configuration_

    setup support for loading basic configuration objects to bootstrap cirrus

    :param package_dir: Location of cirrus managed package if not pwd
    :param gitconfig_file: Path to gitconfig if not ~/.gitconfig
    :returns: Configuration instance

    """
    config_instance = Configuration(None, gitconfig_file=gitconfig_file)
    config_instance.setup_load()
    return config_instance


def get_github_auth():
    """
    _get_git_auth_

    Backwards compatibility accessor for github auth using
    credential plugin
    """
    c = load_configuration()
    r = c.credentials.github_credentials()
    return r['github_user'], r['github_token']


def get_pypi_auth():
    """
    _pypi_auth_

    Get pypi credentials from gitconfig
    DEPRECATED: use Configuration.credentials instead

    """
    c = load_configuration()
    pypi = c.credentials.pypi_credentials()
    ssh = c.credentials.ssh_credentials()
    return {
        'username': pypi['username'],
        'ssh_username': ssh['ssh_username'],
        'ssh_key': ssh['ssh_key'],
        'token': pypi['token']
    }


def get_buildserver_auth():
    """
    _buildserver_auth_

    Get buildserver credentials from gitconfig
    DEPRECATED: use Configuration.credentials instead

    """
    c = load_configuration()
    build = c.credentials.buildserver_credentials()
    return build['buildserver-user'], build['buildserver-token']


def get_chef_auth():
    """
    get chef auth info from gitconfig
    DEPRECATED: use Configuration.credentials instead

    """
    c = load_configuration()
    chef = c.credentials.chef_credentials()
    return {
        'chef_server':  chef['chef-server'],
        'chef_username': chef['chef-username'],
        'chef_keyfile': chef['chef-keyfile'],
        'chef_client_user': chef['chef-client-user'],
        'chef_client_keyfile': chef['chef-client-keyfile']
    }
