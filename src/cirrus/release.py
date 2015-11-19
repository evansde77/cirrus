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
from cirrus.git_tools import build_release_notes
from cirrus.git_tools import branch, checkout_and_pull
from cirrus.git_tools import commit_files, remote_branch_exists
from cirrus.github_tools import GitHubContext
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


def convert_bool(value):
    """helper to make sure bools are bools"""
    if value in (True, False):
        return value
    if value is None:
        return False
    if str(value).lower() in ('true', '1'):
        return True
    return False


def release_config(config, opts):
    """
    _release_config_

    Extract and validate the release config parameters
    from the cirrus config for the package
    """
    release_config_defaults = {
        'wait_on_ci': False,
        'wait_on_ci_develop': False,
        'wait_on_ci_master': False,
        'wait_on_ci_timeout': 600,
        'wait_on_ci_interval': 2,
        'github_context_string': None,
        'update_github_context': False,
    }

    release_config = {}
    if 'release' not in config:
        release_config = release_config_defaults
    else:
        for key, val in release_config_defaults.iteritems():
            release_config[key] = config.get_param('release', key, val)

    release_config['wait_on_ci'] = convert_bool(release_config['wait_on_ci'])
    release_config['wait_on_ci_develop'] = convert_bool(
        release_config['wait_on_ci_develop']
    )
    release_config['wait_on_ci_master'] = convert_bool(
        release_config['wait_on_ci_master']
    )

    if opts.wait_on_ci:
        release_config['wait_on_ci'] = True
    if opts.github_context_string:
        release_config['update_github_context'] = True
        release_config['github_context_string'] = opts.github_context_string

    # validate argument types
    release_config['wait_on_ci_timeout'] = int(
        release_config['wait_on_ci_timeout']
    )
    release_config['wait_on_ci_interval'] = int(
        release_config['wait_on_ci_interval']
    )
    release_config['update_github_context'] = convert_bool(
        release_config['update_github_context']
    )

    if release_config['update_github_context']:
        # require context string
        if release_config['github_context_string'] is None:
            msg = "if using update_github_context you must provide a github_context_string"
            raise RuntimeError(msg)
    return release_config


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

    merge_command = subparsers.add_parser('merge')
    merge_command.add_argument(
        '--wait-on-ci',
        action='store_true',
        dest='wait_on_ci',
        help='Wait for GH CI status to be success before uploading'
    )
    merge_command.add_argument(
        '--context-string',
        default=None,
        dest='github_context_string',
        help='Update the github context string provided when pushed'
    )

    merge_command.add_argument(
        '--cleanup',
        action='store_true',
        dest='cleanup',
        help='Clean up release branch after merging'
    )

    upload_command = subparsers.add_parser('upload')
    upload_command.add_argument(
        '--test',
        action='store_true',
        dest='test',
        help='test only, do not actually push or upload'
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
    # make sure the branch doesnt already exist on remote
    if remote_branch_exists(repo_dir, branch_name):
        msg = (
            "Error: branch {} already exists on the remote repo "
            "Please clean up that branch before proceeding"
            ).format(branch_name)
        LOGGER.error(msg)
        raise RuntimeError(msg)

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


def upload_release(opts):
    """
    _upload_release_
    """
    LOGGER.info("Uploading release...")
    config = load_configuration()

    build_artifact = artifact_name(config)
    LOGGER.info("Uploading artifact: {0}".format(build_artifact))

    if not os.path.exists(build_artifact):
        msg = (
            "Expected build artifact: {0} Not Found, upload aborted\n"
            "Did you run git cirrus release build?"
        ).format(build_artifact)
        LOGGER.error(msg)
        raise RuntimeError(msg)

    # merge in release branches and tag, push to remote
    tag = config.package_version()

    # upload to pypi via fabric over ssh
    if opts.test:
        LOGGER.info("Uploading {} to pypi disabled by test or no-upload option...".format(tag))
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


def merge_release(opts):
    """
    _merge_release_

    Merge a release branch git flow style into master and develop
    branches (or those configured for this package) and tag
    master.

    """
    config = load_configuration()
    rel_conf = release_config(config, opts)
    repo_dir = os.getcwd()
    tag = config.package_version()
    master = config.gitflow_master_name()
    develop = config.gitflow_branch_name()

    with GitHubContext(repo_dir) as ghc:

        release_branch = ghc.active_branch_name
        expected_branch = release_branch_name(config)
        if release_branch != expected_branch:
            msg = (
                "Not on the expected release branch according "
                "to cirrus.conf\n Expected:{0} but on {1}"
            ).format(expected_branch, release_branch)
            LOGGER.error(msg)
            raise RuntimeError(msg)

        # merge release branch into master
        LOGGER.info("Tagging and pushing {0}".format(tag))

        sha = ghc.repo.head.ref.commit.hexsha
        if rel_conf['wait_on_ci']:
            #
            # wait on release branch CI success
            #
            LOGGER.info("Waiting on CI build for {0}".format(release_branch))
            ghc.wait_on_gh_status(
                sha,
                timeout=rel_conf['wait_on_ci_timeout'],
                interval=rel_conf['wait_on_ci_interval']
            )

        if rel_conf['update_github_context']:
            LOGGER.info("Setting {} for {}".format(
                rel_conf['github_context_string'],
                sha)
            )
            ghc.set_branch_state(
                'success',
                rel_conf['github_context_string'],
                branch=sha
            )

        LOGGER.info("Merging {} into {}".format(release_branch, master))
        ghc.pull_branch(master)
        ghc.merge_branch(release_branch)
        sha = ghc.repo.head.ref.commit.hexsha
        if rel_conf['wait_on_ci_master']:
            #
            # wait on release branch CI success
            #
            LOGGER.info("Waiting on CI build for {0}".format(master))
            ghc.wait_on_gh_status(
                sha,
                timeout=rel_conf['wait_on_ci_timeout'],
                interval=rel_conf['wait_on_ci_interval']
            )
        if rel_conf['update_github_context']:
            LOGGER.info("Setting {} for {}".format(
                rel_conf['github_context_string'],
                sha)
            )
            ghc.set_branch_state(
                'success',
                rel_conf['github_context_string'],
                branch=sha
            )
        ghc.push_branch()
        LOGGER.info("Tagging {} as {}".format(master, tag))
        ghc.tag_release(tag, master)

        LOGGER.info("Merging {} into {}".format(release_branch, develop))
        ghc.pull_branch(develop)
        ghc.merge_branch(release_branch)
        sha = ghc.repo.head.ref.commit.hexsha
        if rel_conf['wait_on_ci_develop']:
            #
            # wait on release branch CI success
            #
            LOGGER.info("Waiting on CI build for {0}".format(develop))
            ghc.wait_on_gh_status(
                sha,
                timeout=rel_conf['wait_on_ci_timeout'],
                interval=rel_conf['wait_on_ci_interval']
            )
        if rel_conf['update_github_context']:
            LOGGER.info("Setting {} for {}".format(
                rel_conf['github_context_string'],
                sha)
            )
            ghc.set_branch_state(
                'success',
                rel_conf['github_context_string'],
                branch=sha
            )
        ghc.push_branch()

        if opts.cleanup:
            ghc.delete_branch(release_branch)


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

    if opts.command == 'merge':
        merge_release(opts)

    if opts.command == 'upload':
        upload_release(opts)

    if opts.command == 'build':
        build_release(opts)


if __name__ == '__main__':

    main()
