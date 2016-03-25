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


setuptools.setup(
    name=config.get("package", "name"),
    version=config.get("package", "version"),
    description=config.get("package", "description"),
    package_dir={"":"src"},
    url="https://github.com/evansde77/cirrus",
    author="Dave Evans",
    author_email="evansde77@gmail.com",
    
    packages=setuptools.find_packages("src"),
    entry_points = {
      "console_scripts": scripts,
      "cirrus_commands": scripts
      }
    )
