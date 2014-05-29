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

    def load(self, parser):
        """
        _load_

        :param parser: ConfigParser.RawConfigParser instance that
         has read in the cirrus.conf file

        """
        for section in parser.sections():
            self.setdefault(section, {})
            for option in parser.options(section):
                self[section].setdefault(
                    option,
                    parser.get(section, option)
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

    def update_package_version(self, new_version):
        """
        _update_package_version_

        Update the version in the configuration field
        """


def load_configuration():
    """
    _load_configuration_

    Load the cirrus.conf file and parse it into a nested dictionary
    like Configuration instance.

    :returns: Configuration instance

    """
    config_path = os.path.join(
        os.getcwd(),
        'cirrus.conf'
    )
    if not os.path.exists(config_path):
        msg = "Couldnt find ./cirrus.conf, are you in a package directory?"
        raise RuntimeError(msg)

    config = ConfigParser.RawConfigParser()
    config.read(config_path)
    config_instance = Configuration(config_path)
    config_instance.load(config)
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


if __name__ == '__main__':
    load_configuration()