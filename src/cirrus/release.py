#!/usr/bin/env python
"""
_release_

Implement git cirrus release command


"""
import os
import sys
import time
import datetime
import itertools
from collections import OrderedDict
from fabric.operations import put, local

from argparse import ArgumentParser
from cirrus.configuration import load_configuration
from cirrus.configuration import get_pypi_auth
from cirrus.git_tools import build_release_notes
from cirrus.git_tools import checkout_and_pull, push
from cirrus.git_tools import branch, merge
from cirrus.git_tools import commit_files
from cirrus.git_tools import tag_release, get_active_branch
from cirrus.github_tools import branch_status
from cirrus.github_tools import current_branch_mark_status
from cirrus.utils import update_file, update_version
from cirrus.fabric_helpers import FabricHelper
from cirrus.logger import get_logger
from cirrus.plugins.jenkins import JenkinsClient

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

    # borrow --micro/minor/major options from "new" command.
    subparsers.add_parser('trigger', parents=[new_command], add_help=False)
    subparsers.add_parser('build')

    upload_command = subparsers.add_parser('upload')
    upload_command.add_argument(
        '--test',
        action='store_true',
        dest='test',
        help='test only, do not actually push or upload'
    )
    upload_command.add_argument(
        '--no-upload',
        action='store_true',
        dest='no_upload',
        help='do not upload build artifact to pypi'
    )
    upload_command.add_argument(
        '--pypi-url',
        action='store',
        dest='pypi_url',
        help='upload to specified pypi url'
    )
    upload_command.add_argument(
        '--pypi-sudo',
        action='store_true',
        dest='pypi_sudo',
        help='use sudo to upload build artifact to pypi'
    )
    upload_command.add_argument(
        '--no-pypi-sudo',
        action='store_false',
        dest='pypi_sudo',
        help='do not use sudo to upload build artifact to pypi'
    )
    upload_command.add_argument(
        '--wait-on-ci',
        action='store_true',
        dest='wait_on_ci',
        help='Wait for GH CI status to be success before uploading'
    )
    upload_command.add_argument(
        '--wait-on-ci-timeout',
        type=int,
        default=600,
        dest='wait_on_ci_timeout',
        help='Seconds to wait on CI before abandoning upload'
    )
    upload_command.set_defaults(pypi_sudo=True)

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
    changes = ['cirrus.conf']

    if opts.bump:
        for pkg in opts.bump:
            if '==' not in pkg:
                msg = 'Malformed version expression.  Please use "pkg==0.0.0"'
                LOGGER.error(msg)
                raise RuntimeError(msg)
        try:
            update_requirements('requirements.txt', opts.bump)
            changes.append('requirements.txt')
        except Exception as ex:
            # halt on any problem updating requirements
            LOGGER.exception('Failed to update requirements.txt -- {}'.format(ex))
            raise RuntimeError(ex)

    # update release notes file
    relnotes_file, relnotes_sentinel = config.release_notes()
    if (relnotes_file is not None) and (relnotes_sentinel is not None):
        LOGGER.info('Updating release notes in {0}'.format(relnotes_file))
        relnotes = "Release: {0} Created: {1}\n".format(
            new_version,
            datetime.datetime.utcnow().isoformat()
        )
        relnotes += build_release_notes(
            repo_dir,
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
    return (new_version, field)


def trigger_release(opts):
    """
    _trigger_release_

    Alias for "git cirrus release new --micro/minor/major.
    - Run the "release new" command
    - Capture the new version string
    - Pass new version number to external build server

    Requires the following sections and values in cirrus.conf:

    [build-server]
    name = jenkins

    [jenkins]
    url = http://localhost:8080
    job = default
    """
    config = load_configuration()

    try:
        build_server = config['build-server']['name']
        build_server_config = config[build_server]
    except KeyError:
        msg = (
            '[build-server] section is incomplete or missing from cirrus.conf. '
            'Please see below for an example.\n'
            '\n [build-server]'
            '\n name = jenkins'
            '\n [jenkins]'
            '\n url = http://localhost:8080'
            '\n job = default'
            )
        raise RuntimeError(msg)

    new_version, release_level = new_release(opts)

    if build_server == 'jenkins':
        _trigger_jenkins_release(build_server_config,
                                 new_version,
                                 release_level)


def _trigger_jenkins_release(config, new_version, level):
    """
    _trigger_jenkins_release_

    Performs jenkins specific steps for launching a build job
    """
    client = JenkinsClient(config['url'])
    build_params = {
        'LEVEL': level,
        'VERSION': new_version,
    }

    response = client.start_job(config['job'], build_params)

    if response.status_code != 201:
        LOGGER.error(response.text)
        raise RuntimeError('Jenkins HTTP API returned code {}'.format(response.status_code))


def wait_on_gh_status(branch_name, timeout=600, interval=2):
    """
    _wait_on_gh_status_

    Wait for CI checks to complete for the branch named

    :param branch_name: name of branch to watch
    :param timeout: max wait time in seconds
    :param interval: pause between checks interval in seconds

    """
    time_spent = 0
    status = branch_status(branch_name)
    LOGGER.info("Waiting on CI status of {}...".format(branch_name))
    while status == 'pending':
        if time_spent > timeout:
            LOGGER.error("Exceeded timeout for branch status {}".format(branch_name))
            break
        status = branch_status(branch_name)
        time.sleep(interval)
        time_spent += interval

    if status != 'success':
        msg = "CI Test status is not success: {} is {}".format(branch_name, status)
        LOGGER.error(msg)
        raise RuntimeError(msg)


def upload_release(opts):
    """
    _upload_release_
    """
    LOGGER.info("Uploading release...")
    config = load_configuration()
    release_config = {
        'wait_on_ci': False,
        'wait_on_ci_timeout': 600,
        'wait_on_ci_interval': 2
    }
    if 'release' in config:
        release_config['wait_on_ci'] = config.get_param(
            'release', 'wait_on_ci', False
        )
        release_config['wait_on_ci_timeout'] = int(config.get_param(
            'release', 'wait_on_ci_timeout', 600)
        )
        release_config['wait_on_ci_interval'] = int(config.get_param(
            'release', 'wait_on_ci_interval', 2)
        )
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

    if opts.wait_on_ci:
        release_config['wait_on_ci'] = True
        release_config['wait_on_ci_timeout'] = opts.wait_on_ci_timeout

    if release_config['wait_on_ci']:
        wait_on_gh_status(
            curr_branch,
            timeout=release_config['wait_on_ci_timeout'],
            interval=release_config['wait_on_ci_interval']
        )

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
        if release_config['wait_on_ci']:
            # if wait_on_ci is set and we have gotten to this point,
            # tests pass on the release branch, so we can tell the
            # remote the good news.
            current_branch_mark_status(repo_dir, 'success')
        push(repo_dir)
    do_push = not opts.test
    tag_release(repo_dir, tag, master, push=do_push)

    # Merge release branch back to develop
    # push to develop
    LOGGER.info("Merging back to develop...")
    checkout_and_pull(repo_dir, develop)
    if release_config['wait_on_ci']:
        # @HACK If we are doing CI, our branch will be "out of date",
        # so we update it by merging from master (not gitflow, I
        # know), and then waiting for CI status on the remote.
        merge(repo_dir, develop, master)
        wait_on_gh_status(
            develop,
            timeout=release_config['wait_on_ci_timeout'],
            interval=release_config['wait_on_ci_interval']
        )
    else:
        merge(repo_dir, develop, expected_branch)

    if not opts.test:
        LOGGER.info("pushing to remote...")
        if release_config['wait_on_ci']:
            # if wait_on_ci is set and we have gotten to this point,
            # tests pass on the release branch, so we can tell the
            # remote the good news.
            current_branch_mark_status(repo_dir, 'success')
        push(repo_dir)
    LOGGER.info("Release {0} has been tagged and uploaded".format(tag))
    # TODO: clean up release branch

    # upload to pypi via fabric over ssh
    if opts.no_upload or opts.test:
        LOGGER.info("Uploading to pypi disabled by test or no-upload option...")
    else:
        pypi_conf = config.pypi_config()
        pypi_auth = get_pypi_auth()
        if opts.pypi_url:
            pypi_url = opts.pypi_url
        else:
            pypi_url = pypi_conf['pypi_url']
        if pypi_auth['ssh_username'] is not None:
            pypi_user = pypi_auth['ssh_username']
        else:
            pypi_user = pypi_auth['username']
        package_dir = pypi_conf['pypi_upload_path']
        LOGGER.info("Uploading {0} to {1}".format(build_artifact, pypi_url))
        with FabricHelper(
                pypi_url,
                pypi_user,
                pypi_auth['ssh_key']):

            # fabric put the file onto the pypi server
            put(build_artifact, package_dir, use_sudo=opts.pypi_sudo)

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
    ['foo==0.0.9', 'bar==1.2']
    """
    LOGGER.info('Updating {}'.format(path))

    with open(path, 'r+') as fh:
        # original requirements.txt in its pristine order
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

    if opts.command == 'trigger':
        trigger_release(opts)

    if opts.command == 'upload':
        upload_release(opts)

    if opts.command == 'build':
        build_release(opts)


if __name__ == '__main__':

    main()
