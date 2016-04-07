#!/usr/bin/env python
"""
_selfupdate_

Util command for updating the cirrus install itself
Supports getting a spefified branch or tag, or defaults to
looking up the latest release and using that instead.

"""
import sys
import argparse
import arrow
import os
import requests
import inspect
import contextlib

from fabric.operations import local

import cirrus
from cirrus.configuration import load_configuration
from cirrus.environment import cirrus_home, virtualenv_home
from cirrus.github_tools import get_releases
from cirrus.git_tools import update_to_branch, update_to_tag
from cirrus.logger import get_logger


LOGGER = get_logger()
PYPI_JSON_URL = "https://pypi.python.org/pypi/cirrus-cli/json"


@contextlib.contextmanager
def chdir(dirname=None):
    curdir = os.getcwd()
    try:
        if dirname is not None:
            os.chdir(dirname)
        yield
    finally:
        os.chdir(curdir)


def build_parser(argslist):
    """
    _build_parser_

    Set up command line parser for the selfupdate command

    """
    parser = argparse.ArgumentParser(
        description=(
            'git cirrus selfupdate command, '
            'used to update cirrus itself'
            )
    )
    parser.add_argument('command', nargs='?')
    parser.add_argument(
        '--version',
        help='specify a tag to install',
        required=False,
        default=None,

    )
    parser.add_argument(
        '--branch',
        help='specify a branch to use',
        required=False,
        default=None,
    )
    parser.add_argument(
        '--legacy-repo',
        help='Use the old, non pip update process',
        required=False,
        dest='legacy_repo',
        action='store_true',
        default=False,
    )

    opts = parser.parse_args(argslist)
    return opts


def sort_by_date(d1, d2):
    """
    cmp function to sort by datetime string
    that is second element of tuples in list
    """
    date1 = arrow.get(d1[1])
    date2 = arrow.get(d2[1])
    return date1 > date2


def latest_release(config):
    """
    _latest_release_

    pull list of releases from GH repo, pick the newest by
    publication date.

    """
    releases = get_releases(config.organisation_name(), config.package_name())
    tags = [(release['tag_name'], release['published_at']) for release in releases]
    sorted(tags, cmp=sort_by_date)
    most_recent_tag = tags[0][0]
    return most_recent_tag


def latest_pypi_release():
    """grab latest release from pypi"""
    resp = requests.get(PYPI_JSON_URL)
    resp.raise_for_status()
    content = resp.json()
    latest = content['info']['version']
    return latest


def find_cirrus_install():
    """
    _find_cirrus_install_

    Use inspect to find root path of install so we
    can cd there and run the cirrus updates in the right location

    The install process will check out the cirrus repo, the cirrus
    module will be in src/cirrus of that dir

    """
    cirrus_mod = os.path.dirname(inspect.getsourcefile(cirrus))
    src_dir = os.path.dirname(cirrus_mod)
    cirrus_dir = os.path.dirname(src_dir)
    return cirrus_dir


def setup_develop(config):
    """
    _setup_develop_

    run local python setup.py develop via fab

    """
    LOGGER.info("running setup.py develop...")
    local(
        'git cirrus build --upgrade'
    )

    local(
        ' . ./{0}/bin/activate && python setup.py develop'.format(
            config.venv_name()
        )
    )
    return


def pip_install(version):
    """pip install the version of cirrus requested"""
    pip_req = 'cirrus-cli=={0}'.format(version)
    venv_name = os.path.basename(virtualenv_home())
    LOGGER.info("running pip upgrade...")
    local(
        ' . ./{0}/bin/activate && pip install --upgrade {1}'.format(
            venv_name, pip_req
        )
    )


def legacy_update(opts):
    """update repo installed cirrus"""
    install = find_cirrus_install()
    with chdir(install):
        config = load_configuration()

        if opts.branch and opts.version:
            msg = "Can specify branch -OR- version, not both"
            raise RuntimeError(msg)

        if opts.branch is not None:
            update_to_branch(opts.branch, config)
            setup_develop(config)
            return

        if opts.version is not None:
            tag = opts.version
        else:
            tag = latest_release(config)
            LOGGER.info("Retrieved latest tag: {0}".format(tag))
        update_to_tag(tag, config)
        setup_develop(config)


def pip_update(opts):
    """update pip installed cirrus"""
    install = cirrus_home()
    with chdir(install):
        if opts.version is not None:
            tag = opts.version
            LOGGER.info("tag specified: {0}".format(tag))
        else:
            # should probably be a pip call now...
            tag = latest_pypi_release()
            LOGGER.info("Retrieved latest tag: {0}".format(tag))
        pip_install(tag)


def main():
    """
    _main_

    parse command line opts and deduce wether to check out
    a branch or tag, default behaviour is to look up latest
    release on github and install that

    """
    opts = build_parser(sys.argv)
    if opts.legacy_repo:
        legacy_update(opts)
    else:
        pip_update(opts)
    return

if __name__ == '__main__':
    main()
