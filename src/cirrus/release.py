#!/usr/bin/env python
"""
_release_

Implement git cirrus release command


"""
import os
import datetime
import itertools
from fabric.operations import put, local

from argparse import ArgumentParser
from cirrus.configuration import load_configuration
from cirrus.git_tools import build_release_notes
from cirrus.git_tools import checkout_and_pull
from cirrus.git_tools import branch
from cirrus.git_tools import commit_files
from cirrus.utils import update_file, update_version
from cirrus.fabric_helpers import FabricHelper


def highlander(iterable):
    """check only single True value in iterable"""
    # There Can Be Only One!!!
    i = iter(iterable)
    return any(i) and not any(i)


def parse_version(version):
    """
    _parse_version_

    Parse semantic major.minor.micro version string

    :param version: X.Y.Z format version string

    :returns: dictionary containing major, minor, micro versions
    as integers

    """
    split = version.split('.', 2)
    return {
        'major': int(split[0]),
        'minor': int(split[1]),
        'micro': int(split[2]),
    }


def bump_version_field(version, field='major'):
    """
    parse the version and increment the major, minor or micro
    version specified by field
    Return the updated version string
    """
    vers_params = parse_version(version)
    vers_params[field] += 1
    return "{major}.{minor}.{micro}".format(**vers_params)


def artifact_name(config):
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


def build_parser(argslist):
    """
    _build_parser_

    Set up command line parser for the release command

    """
    parser = ArgumentParser(
        description='git cirrus release command'
    )
    parser.add_argument('command', nargs='?')

    subparsers = parser.add_subparsers(dest='command')
    new_command = subparsers.add_parser('new')
    new_command.add_argument(
        '--micro',
        action='store_true',
        dest='micro'
    )
    new_command.add_argument(
        '--minor',
        action='store_true',
        dest='minor'
    )
    new_command.add_argument(
        '--major',
        action='store_true',
        dest='major'
    )

    build_command = subparsers.add_parser('build')

    publish_command = subparsers.add_parser('publish')

    opts = parser.parse_args(argslist)
    return opts


def new_release(opts):
    """
    _new_release_

    - Create a new release branch in the local repo
    - Edit the conf to bump the version
    - Edit the history file with release notes

    """
    if not highlander( [opts.major, opts.minor, opts.micro]):
        msg = "Can only specify one of --major, --minor or --micro"
        raise RuntimeError(msg)



    fields = ['major', 'minor', 'micro']
    mask = [opts.major, opts.minor, opts.micro]
    field = [ x for x in itertools.compress(fields, mask)][0]

    config = load_configuration()

    # version bump:
    current_version = config.package_version()
    new_version = bump_version_field(current_version, field)

    # release branch
    branch_name = "{0}{1}".format(
        config.gitflow_release_prefix(),
        new_version
    )

    # need to be on the latest develop
    repo_dir = os.getcwd()
    main_branch = config.gitflow_branch_name()
    checkout_and_pull(repo_dir,  main_branch)

    # create release branch
    branch(repo_dir, branch_name, main_branch)

    # update cirrus conf
    config.update_package_version(new_version)
    changes = ['cirrus.conf']

    # update release notes file
    relnotes_file, relnotes_sentinel = config.release_notes()
    if (relnotes_file is not None) and (relnotes_sentinel is not None):
        relnotes = "Release: {0} Created: {1}\n".format(
            new_version,
            datetime.datetime.utcnow().isoformat()
        )
        relnotes += build_release_notes(
            config.organisation_name(),
            config.package_name(),
            current_version
        )
        update_file(relnotes_file, relnotes_sentinel, relnotes)
        changes.append(relnotes_file)

    # update __version__ or equivalent
    version_file, version_attr = config.version_file()
    if version_file is not None:
        update_version(version_file, new_version, version_attr)
        changes.append(version_file)

    # update files changed
    msg = "cirrus release: new release created for {0}".format(branch_name)
    commit_files(repo_dir, msg, *changes)
    return


def upload_release(opts):
    """
    _upload_release_
    """
    config = load_configuration()
    build_artifact = artifact_name(config)
    if not os.path.exists(build_artifact):
        msg = (
            "Expected build artifact: {0} Not Found, upload aborted\n"
            "Did you run git cirrus release build?"
        )
        raise RuntimeError(msg)

    pypi_conf = config.pypi_config()
    package_dir = pypi_conf['pypi_upload_path']
    with FabricHelper(
            pypi_conf['pypi_hostname'],
            pypi_conf['pypi_username'],
            pypi_conf['pypi_ssh_key']):

        # fabric put the file onto the pypi server
        put(build_artifact, package_dir, use_sudo=True)

    #TODO:
    # Merge release branch to master and tag
    # push to master
    # Merge release branch back to develop
    # push to develop


def build_release(opts):
    """
    _build_release_

    run python setup.py sdist to create the release artifact

    """
    config = load_configuration()
    local('python setup.py sdist')
    build_artifact = artifact_name(config)
    if not os.path.exists(build_artifact):
        msg = "Expected build artifact: {0} Not Found".format(build_artifact)
        raise RuntimeError(msg)
    return build_artifact


def main(argslist):
    opts = build_parser(argslist)
    if opts.command == 'new':
        new_release(opts)

    if opts.command == 'upload':
        upload_release(opts)

    if opts.command == 'build':
        build_release(opts)


if __name__ == '__main__':

    main(['publish'])
