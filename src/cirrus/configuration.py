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
import gitconfig
import ConfigParser


class Configuration(dict):
    """
    _Configuration_

    """
    def __init__(self, config_file):
        super(Configuration, self).__init__(self)
        self.config_file = config_file
        self.parser = None

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

    def pypi_url(self):
        return self.get('pypi', {}).get('pypi_url')

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

    def venv_name(self):
        return self.get('build', {}).get('virtualenv_name', 'venv')

    def quality_rcfile(self):
        return self.get('quality', {}).get('rcfile')

    def quality_threshold(self):
        return self.get('quality', {}).get('threshold')

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


def load_configuration(package_dir=None):
    """
    _load_configuration_

    Load the cirrus.conf file and parse it into a nested dictionary
    like Configuration instance.

    :params package_dir: Location of cirrus managed package if not pwd
    :returns: Configuration instance

    """
    dirname = os.getcwd()
    if package_dir is not None:
        dirname = package_dir

    config_path = os.path.join(dirname, 'cirrus.conf')

    if not os.path.exists(config_path):
        msg = "Couldnt find ./cirrus.conf, are you in a package directory?"
        raise RuntimeError(msg)

    config_instance = Configuration(config_path)
    config_instance.load()
    return config_instance


def get_github_auth():
    """
    _get_git_auth_

    Pull in github auth user & token from gitconfig
    """
    gitconfig_file = os.path.join(os.environ['HOME'], '.gitconfig')
    config = gitconfig.config(gitconfig_file)
    github_user = config.get('cirrus', 'github-user')
    github_token = config.get('cirrus', 'github-token')
    return github_user, github_token


def get_pypi_auth():
    """
    _pypi_auth_

    Get pypi credentials from gitconfig

    """
    gitconfig_file = os.path.join(os.environ['HOME'], '.gitconfig')
    config = gitconfig.config(gitconfig_file)
    pypi_user = config.get('cirrus', 'pypi-user')
    pypi_key = config.get('cirrus', 'pypi-ssh-key')
    pypi_token = config.get('cirrus', 'pypi-token')
    return {
        'username': pypi_user,
        'ssh_key': pypi_key,
        'token': pypi_token
    }


if __name__ == '__main__':
    load_configuration()
