#!/usr/bin/env python
"""
_setup.py_

Setup script for cirrus.

"""
import ConfigParser
import setuptools

#
# read the cirrus conf for this package
#
config = ConfigParser.RawConfigParser()
config.read("cirrus.conf")

#
# grab the commands to be installed from thr cirrus conf
#
scripts = [
    "{0}={1}".format(key, config.get('commands', key))
    for key in config.options("commands")
]

requirements_file = open('requirements.txt')

# Manually parse the requirements file. Pip 1.5.6 to 6.0 has a function
# behavior change for pip.req.parse_requirements. You must use the setuptools
# format when specifying requirements.
#  - https://pythonhosted.org/setuptools/setuptools.html#declaring-dependencies
# Furthermore, you can't use line continuations with the following:
requirements = requirements_file.read().strip().split('\n')


setuptools.setup(
    name=config.get("package", "name"),
    version=config.get("package", "version"),
    description=config.get("package", "description"),
    package_dir={"":"src"},
    url="https://github.com/evansde77/cirrus",
    author="Dave Evans",
    author_email="evansde77@gmail.com",
    include_package_data=True,
    install_requires=requirements,    
    packages=setuptools.find_packages("src"),
    entry_points = {
      "console_scripts": scripts,
      "cirrus_commands": scripts
      }
    )
