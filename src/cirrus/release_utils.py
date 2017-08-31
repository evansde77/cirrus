#!/usr/bin/env python

import re
import datetime

from cirrus.configuration import load_configuration

DEFAULT_FORMAT = "%Y%m%d"


def nightly_config(conf=None):
    """
    get the nightly config settings from
    the release section

    """
    result = {
        "nightly_format": DEFAULT_FORMAT,
        "nightly_separator": "-nightly-"
    }
    if not conf:
        conf = load_configuration()
    if not conf.has_section('release'):
        return result
    result['nightly_format'] = conf.get_param("release", "nightly_format", result['nightly_format'])
    result['nightly_separator'] = conf.get_param("release", "nightly_separator", result['nightly_separator'])
    return result


def is_nightly(version):
    """
    return True/False if the version string
    provided matches a nightly format.

    """
    conf = nightly_config()
    reg = "^[0-9]+\.[0-9]+\.[0-9]+{}".format(conf['nightly_separator'])
    matcher = re.compile(reg)
    elems = matcher.split(version, 1)
    if len(elems) == 2:
        return True
    return False


def new_nightly():
    """
    generate a new nightly version

    """
    cirrus_conf = load_configuration()
    nightly_conf = nightly_config(cirrus_conf)
    now = datetime.datetime.now()
    ts = now.strftime(nightly_conf['nightly_format'])
    current = cirrus_conf.package_version()

    nightly = "{version}{sep}{ts}".format(
        version=current,
        sep=nightly_conf['nightly_separator'],
        ts=ts
    )
    return nightly


def remove_nightly(ghc):
    """
    remove the nightly part from the cirrus.conf version
    """
    cirrus_conf = load_configuration()
    nightly_conf = nightly_config(cirrus_conf)
    current = cirrus_conf.package_version()
    if is_nightly(current):
        new_version = current.split(nightly_conf['nightly_separator'], 1)[0]
        cirrus_conf.update_package_version(new_version)
        ghc.commit_files_optional_push(
            "remove nightly tag from cirrus.conf",
            False,
            "cirrus.conf"
        )
    return
