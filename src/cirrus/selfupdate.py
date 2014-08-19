#!/usr/bin/env python
"""
_selfupdate_

Util command for updating the cirrus install itself
Supports getting a spefified branch or tag, or defaults to
looking up the latest release and using that instead.

"""
import sys
import git
import argparse
import arrow
import os

from fabric.operations import local

from cirrus.configuration import load_configuration
from cirrus.github_tools import get_releases
from cirrus.logger import get_logger


LOGGER = get_logger()


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
    tags = [ (release['tag_name'], release['published_at']) for release in releases  ]
    sorted(tags, cmp=sort_by_date)
    most_recent_tag = tags[0][0]
    return most_recent_tag


def setup_develop(config):
    """
    _setup_develop_

    run local python setup.py develop via fab

    """
    LOGGER.info("running setup.py develop...")
    local(
        ' . ./{0}/bin/activate && python setup.py develop'.format(
            config.venv_name()
        )
    )


def update_to_branch(branch, config, origin='origin'):
    """
    checkout specified branch and run setup.py develop
    """
    LOGGER.info(
        "selfupdate running, will switch to branch {0}".format(
            branch
        )
    )
    repo_dir = os.getcwd()

    LOGGER.info("fetching remotes...")
    r = git.Repo(repo_dir)
    r.remotes[origin].fetch()

    g = git.Git()
    LOGGER.info("checking out {0}...".format(branch))
    g.checkout('{0}/{1}'.format(origin, branch), b=branch)

    branch_ref = r.heads[branch]
    branch_ref.checkout()

    setup_develop(config)
    return


def update_to_tag(tag, config, origin='origin'):
    """
    checkout specified tag, and run setup.py develop
    """
    LOGGER.info(
        "selfupdate running, will switch to tag {0}".format(
            tag
        )
    )
    repo_dir = os.getcwd()

    LOGGER.info("fetching remote tags...")
    r = git.Repo(repo_dir)
    r.remotes[origin].fetch(tags=True)

    ref = r.tags[tag]
    LOGGER.info("checking out {0}...".format(tag))
    g = git.Git()
    g.checkout(ref)

    setup_develop(config)
    return



def main():
    """
    _main_

    parse command line opts and deduce wether to check out
    a branch or tag, default behaviour is to look up latest
    release on github and install that

    """
    opts = build_parser(sys.argv)
    config = load_configuration()
    if opts.branch and opts.version:
        msg = "Can specify branch -OR- version, not both"
        raise RuntimeError(msg)

    if opts.branch is not None:
        return update_to_branch(opts.branch, config)

    if opts.version is not None:
        tag = opts.version
    else:
        tag = latest_release(config)
        LOGGER.info("Retrieved latest tag: {0}".format(tag))
    return update_to_tag(tag, config)


if __name__ == '__main__':
    main()
