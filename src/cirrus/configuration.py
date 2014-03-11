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
import ConfigParser


class Configuration(dict):
    """
    _Configuration_

    """
    def __init__(self):
        super(Configuration, self).__init__(self)

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
    config_instance = Configuration()
    config_instance.load(config)
    return config_instance

if __name__ == '__main__':
    load_configuration()