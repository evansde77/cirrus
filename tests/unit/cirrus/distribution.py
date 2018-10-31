#!/usr/bin/env python
"""
distribution helpers for building source, egg and wheels
from packages

"""
import os
from cirrus.build import get_builder_plugin


class ArtifactBuilder(object):


    def __init__(self, config, release):
        self._config
        self._release = release
        self._builder = get_builder_plugin()

    @property
    def source_artifact(self):
        artifact_name = "{0}-{1}.tar.gz".format(
            self._config.package_name(),
            self._config.package_version()
        )
        build_artifact = os.path.join(
            os.getcwd(),
            'dist',
            artifact_name
        )
        return build_artifact

def egg_artifact_name(config):
    """
    given cirrus config, build the expected
    artifact name
    """
    artifact_name = "{0}-{1}.tar.gz".format(
        config.package_name(),
        config.package_version()
    )
    build_artifact = os.path.join(
        os.getcwd(),
        'dist',
        artifact_name
    )
    return build_artifact

def wheel_artifact_name(config):
    """
    given cirrus config, build the expected
    artifact name
    """
    artifact_name = "{0}-{1}.tar.gz".format(
        config.package_name(),
        config.package_version()
    )
    build_artifact = os.path.join(
        os.getcwd(),
        'dist',
        artifact_name
    )
    return build_artifact