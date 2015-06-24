#!/usr/bin/env python
"""
_release_

Implement git cirrus release command


"""
import os
import sys
import datetime
import itertools
from collections import OrderedDict
from fabric.operations import put, local

from argparse import ArgumentParser
from cirrus.configuration import load_configuration
from cirrus.configuration import get_pypi_auth
from cirrus.github_tools import build_release_notes
from cirrus.git_tools import checkout_and_pull, push
from cirrus.git_tools import branch, merge
from cirrus.git_tools import commit_files
from cirrus.git_tools import tag_release, get_active_branch
from cirrus.utils import update_file, update_version
from cirrus.fabric_helpers import FabricHelper
from cirrus.logger import get_logger


LOGGER = get_logger()


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
    parse the version and update the major, minor and micro
    version specified by field
    Return the updated version string
    """
    vers_params = parse_version(version)
    vers_params[field] += 1
    if field == 'major':
        vers_params['minor'] = 0
        vers_params['micro'] = 0
    elif field == 'minor':
        vers_params['micro'] = 0

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


def release_branch_name(config):
    """
    build expected release branch name from current config

    """
    branch_name = "{0}{1}".format(
        config.gitflow_release_prefix(),
        config.package_version()
    )
    return branch_name


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
    new_command.add_argument(
        '--bump',
        nargs='+',
        help='package versions (pkg==0.0.0) to update in requirements.txt'
    )

    build_command = subparsers.add_parser('build')

    upload_command = subparsers.add_parser('upload')
    upload_command.add_argument(
        '--test',
        action='store_true',
        dest='test',
        help="test only, do not actually push or upload"
    )
    upload_command.add_argument(
        '--no-upload',
        action='store_true',
        dest='no_upload',
        help="do not upload build artifact to pypi"
    )

    opts = parser.parse_args(argslist)
    return opts


def new_release(opts):
    """
    _new_release_

    - Create a new release branch in the local repo
    - Edit the conf to bump the version
    - Edit the history file with release notes

    """
    LOGGER.info("Creating new release...")
    if not highlander([opts.major, opts.minor, opts.micro]):
        msg = "Can only specify one of --major, --minor or --micro"
        LOGGER.error(msg)
        raise RuntimeError(msg)

    fields = ['major', 'minor', 'micro']
    mask = [opts.major, opts.minor, opts.micro]
    field = [x for x in itertools.compress(fields, mask)][0]

    config = load_configuration()

    if opts.bump:
        for pkg in opts.bump:
            if '==' not in pkg:
                msg = 'Malformed version expression.  Please use "pkg==0.0.0"'
                LOGGER.error(msg)
                raise RuntimeError(msg)

        update_requirements('requirements.txt', opts.bump)

    # version bump:
    current_version = config.package_version()
    new_version = bump_version_field(current_version, field)

    # release branch
    branch_name = "{0}{1}".format(
        config.gitflow_release_prefix(),
        new_version
    )
    LOGGER.info('release branch is {0}'.format(branch_name))

    # need to be on the latest develop
    repo_dir = os.getcwd()
    main_branch = config.gitflow_branch_name()
    checkout_and_pull(repo_dir,  main_branch)

    # create release branch
    branch(repo_dir, branch_name, main_branch)

    # update cirrus conf
    config.update_package_version(new_version)
    changes = ['cirrus.conf', 'requirements.txt']

    # update release notes file
    relnotes_file, relnotes_sentinel = config.release_notes()
    if (relnotes_file is not None) and (relnotes_sentinel is not None):
        LOGGER.info('Updating release notes in {0}'.format(relnotes_file))
        relnotes = "Release: {0} Created: {1}\n".format(
            new_version,
            datetime.datetime.utcnow().isoformat()
        )
        relnotes += build_release_notes(
            config.organisation_name(),
            config.package_name(),
            current_version,
            config.release_notes_format()
        )
        update_file(relnotes_file, relnotes_sentinel, relnotes)
        changes.append(relnotes_file)

    # update __version__ or equivalent
    version_file, version_attr = config.version_file()
    if version_file is not None:
        LOGGER.info('Updating {0} attribute in {1}'.format(version_file, version_attr))
        update_version(version_file, new_version, version_attr)
        changes.append(version_file)

    # update files changed
    msg = "cirrus release: new release created for {0}".format(branch_name)
    LOGGER.info('Committing files: {0}'.format(','.join(changes)))
    LOGGER.info(msg)
    commit_files(repo_dir, msg, *changes)
    return


def upload_release(opts):
    """
    _upload_release_
    """
    LOGGER.info("Uploading release...")
    config = load_configuration()
    build_artifact = artifact_name(config)
    LOGGER.info("Uploading artifact: {0}".format(build_artifact))
    repo_dir = os.getcwd()
    curr_branch = get_active_branch(repo_dir)
    expected_branch = release_branch_name(config)

    if curr_branch.name != expected_branch:
        msg = (
            "Not on the expected release branch according "
            "to cirrus.conf\n Expected:{0} but on {1}"
        ).format(expected_branch, curr_branch)
        LOGGER.error(msg)
        raise RuntimeError(msg)

    if not os.path.exists(build_artifact):
        msg = (
            "Expected build artifact: {0} Not Found, upload aborted\n"
            "Did you run git cirrus release build?"
        ).format(build_artifact)
        LOGGER.error(msg)
        raise RuntimeError(msg)

    # upload to pypi via fabric over ssh
    if opts.no_upload or opts.test:
        LOGGER.info("Uploading to pypi disabled by test or no-upload option...")
    else:
        pypi_conf = config.pypi_config()
        pypi_auth = get_pypi_auth()
        package_dir = pypi_conf['pypi_upload_path']
        LOGGER.info("Uploading {0} to {1}".format(build_artifact, pypi_conf['pypi_url']))
        with FabricHelper(
                pypi_conf['pypi_url'],
                pypi_auth['username'],
                pypi_auth['ssh_key']):

            # fabric put the file onto the pypi server
            put(build_artifact, package_dir, use_sudo=True)

    # merge in release branches and tag, push to remote
    tag = config.package_version()
    master = config.gitflow_master_name()
    develop = config.gitflow_branch_name()

    # merge release branch into master
    LOGGER.info("Tagging and pushing {0}".format(tag))
    checkout_and_pull(repo_dir, master)
    merge(repo_dir, master, expected_branch)

    if not opts.test:
        LOGGER.info("pushing to remote...")
        push(repo_dir)
    do_push = not opts.test
    tag_release(repo_dir, tag, master, push=do_push)

    # Merge release branch back to develop
    # push to develop
    LOGGER.info("Merging back to develop...")
    checkout_and_pull(repo_dir, develop)
    merge(repo_dir, develop, expected_branch)
    if not opts.test:
        LOGGER.info("pushing to remote...")
        push(repo_dir)
    LOGGER.info("Release {0} has been tagged and uploaded".format(tag))
    # TODO: clean up release branch
    return


def build_release(opts):
    """
    _build_release_

    run python setup.py sdist to create the release artifact

    """
    LOGGER.info("Building release...")
    config = load_configuration()
    local('python setup.py sdist')
    build_artifact = artifact_name(config)
    if not os.path.exists(build_artifact):
        msg = "Expected build artifact: {0} Not Found".format(build_artifact)
        LOGGER.error(msg)
        raise RuntimeError(msg)
    LOGGER.info("Release artifact created: {0}".format(build_artifact))
    return build_artifact


def update_requirements(path, versions):
    """
    _update_requirements_

    Update requirements.txt with the provided versions list, where each item in
    such a list looks exactly like a version specifier in a requirements.txt
    file.  Items without '==' are ignored.

    Example:
    ['foo==0.0.9', 'bar==1.2]
    """
    LOGGER.info('Updating {}'.format(path))

    with open(path, 'r+') as fh:
        # original requirements.txt it its pristine order
        reqs = OrderedDict(tuple(pkg.split('=='))
                           for pkg in fh.readlines() if '==' in pkg)

        for pkg in versions:
            new_pkg, new_version = pkg.split('==')
            reqs[new_pkg] = '{}\n'.format(new_version)
            LOGGER.info('{}=={}'.format(new_pkg, new_version))

        # overwrite original requirements.txt with updated version
        fh.seek(0)
        fh.writelines(['{}=={}'.format(pkg, version)
                      for pkg, version in reqs.iteritems()])
        fh.truncate()


def main():
    opts = build_parser(sys.argv)
    if opts.command == 'new':
        new_release(opts)

    if opts.command == 'upload':
        upload_release(opts)

    if opts.command == 'build':
        build_release(opts)


if __name__ == '__main__':

    main()
