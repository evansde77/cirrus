#!/usr/bin/env python
"""
_twine_helpers_

Helper functions around the Twine CLI/API

"""

from cirrus.configuration import load_configuration
from twine.commands.register import register
from twine.commands.upload import upload


def register_package(
        package,
        repository,
        pypirc='~/.pypirc',
        username=None,
        password=None,
        certfile=None,
        client_certfile=None,
        comment=None
        ):
    """
    :param package: - sdist/bdist etc artifact to register
    :param repository:

    """
    cirrus_conf = load_configuration()
    if cirrus_conf.has_section('twine'):
        username = username or cirrus_conf.get_param('twine', 'username', None)
        password = password or cirrus_conf.get_param('twine', 'password', None)
        certfile = certfile or cirrus_conf.get_param('twine', 'certfile', None)
        client_certfile = client_certfile or cirrus_conf.get_param('twine', 'client_certfile', None)

    register(
        package,
        repository,
        username,
        password,
        comment,
        pypirc,
        certfile,
        client_certfile,
        None
    )


def upload_package(
        package,
        repository,
        pypirc='~/.pypirc',
        sign=False,
        identity=None,
        username=None,
        password=None,
        comment=None,
        sign_with=None,
        skip_existing=False,
        certfile=None,
        client_certfile=None
        ):
    """
    :param package: path to sdist package
    :param repository: repo name to upload to
    :param pypirc: path to pypirc file

    """
    cirrus_conf = load_configuration()
    if cirrus_conf.has_section('twine'):
        username = username or cirrus_conf.get_param('twine', 'username', None)
        password = password or cirrus_conf.get_param('twine', 'password', None)
        certfile = certfile or cirrus_conf.get_param('twine', 'certfile', None)
        identity = identity or cirrus_conf.get_param('twine', 'identity', None)
        sign_with = sign_with or cirrus_conf.get_param('twine', 'sign_with', None)
        client_certfile = client_certfile or cirrus_conf.get_param('twine', 'client_certfile', None)

    upload(
        [package],
        repository,
        sign,
        identity,
        username,
        password,
        comment,
        sign_with,
        pypirc,
        skip_existing,
        certfile,
        client_certfile,
        None
    )
