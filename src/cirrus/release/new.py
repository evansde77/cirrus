import datetime
import itertools
import os


from cirrus.configuration import load_configuration
from cirrus.environment import repo_directory
from cirrus.git_tools import current_branch, has_unstaged_changes, commit_files_optional_push, remote_branch_exists, \
    checkout_and_pull, branch, build_release_notes
from cirrus.github_tools import unmerged_releases
from cirrus.plugins.jenkins import JenkinsClient
from cirrus.release.utils import highlander, bump_version_field, new_nightly
from cirrus.req_utils import bump_package
from cirrus.utils import max_version, update_version, update_file
from cirrus.logger import get_logger


LOGGER = get_logger()


def make_new_version(opts):
    LOGGER.info("Updating package version...")
    if not highlander([opts.major, opts.minor, opts.micro]):
        msg = "Can only specify one of --major, --minor or --micro"
        LOGGER.error(msg)
        raise RuntimeError(msg)

    fields = ['major', 'minor', 'micro']
    mask = [opts.major, opts.minor, opts.micro]
    field = [x for x in itertools.compress(fields, mask)][0]

    config = load_configuration()
    current_version = config.package_version()

    # need to be on the latest develop
    repo_dir = repo_directory()
    curr_branch = current_branch(repo_dir)
    # make sure repo is clean
    if has_unstaged_changes(repo_dir):
        msg = (
            "Error: Unstaged changes are present on the branch {}"
            "Please commit them or clean up before proceeding"
        ).format(curr_branch)
        LOGGER.error(msg)
        raise RuntimeError(msg)

    #
    # compute next version
    #
    if opts.skip_existing:
        # skip any existing unmerged branches
        unmerged = unmerged_releases(repo_dir, version_only=True)
        if unmerged:
            LOGGER.info(
                (
                    "Skipping Existing Versions found "
                    "unmerged_releases: {}"
                ).format(
                    ' '.join(unmerged)
                )
            )
            unmerged.append(current_version)
            current_version = max_version(*unmerged)
            LOGGER.info(
                "selected current version as {}".format(current_version)
            )

    new_version = bump_version_field(current_version, field)
    msg = "Bumping version from {prev} to {new} on branch {branch}".format(
        prev=current_version,
        new=new_version,
        branch=curr_branch
    )
    LOGGER.info(msg)
    # update cirrus conf
    config.update_package_version(new_version)
    changes = ['cirrus.conf']

    if opts.bump:
        reqs_file = os.path.join(repo_dir, 'requirements.txt')
        for pkg, version in opts.bump:
            LOGGER.info("Bumping dependency {} to {}".format(pkg, version))
            bump_package(reqs_file, pkg, version)
        changes.append(reqs_file)

    # update __version__ or equivalent
    version_file, version_attr = config.version_file()
    if version_file is not None:
        LOGGER.info('Updating {0} attribute in {1}'.format(version_file, version_attr))
        update_version(version_file, new_version, version_attr)
        changes.append(version_file)

    # update files changed
    msg = "cirrus release: version bumped for {0}".format(curr_branch)
    LOGGER.info('Committing files: {0}'.format(','.join(changes)))
    LOGGER.info(msg)
    commit_files_optional_push(repo_dir, msg, not opts.no_remote, *changes)


def new_release(opts):
    """
    _new_release_

    - Create a new release branch in the local repo
    - Edit the conf to bump the version
    - Edit the history file with release notes

    """
    LOGGER.info("Creating new release...")
    config = load_configuration()
    current_version = config.package_version()
     # need to be on the latest develop
    repo_dir = repo_directory()

    if opts.nightly:
        msg = "creating new nightly release..."
        new_version = new_nightly()
        field = 'nightly'
    else:
        if not highlander([opts.major, opts.minor, opts.micro]):
            msg = "Can only specify one of --major, --minor or --micro"
            LOGGER.error(msg)
            raise RuntimeError(msg)

        fields = ['major', 'minor', 'micro']
        mask = [opts.major, opts.minor, opts.micro]
        field = [x for x in itertools.compress(fields, mask)][0]
        curr = current_version
        if opts.skip_existing:
            # skip any existing unmerged branches
            unmerged = unmerged_releases(repo_dir, version_only=True)
            if unmerged:
                LOGGER.info(
                    (
                        "Skipping Existing Versions found "
                        "unmerged_releases: {}"
                    ).format(
                        ' '.join(unmerged)
                    )
                )
                unmerged.append(current_version)
                curr = max_version(*unmerged)
                LOGGER.info(
                    "selected current version as {}".format(curr)
                )

        new_version = bump_version_field(curr, field)


    # release branch
    branch_name = "{0}{1}".format(
        config.gitflow_release_prefix(),
        new_version
    )
    LOGGER.info('release branch is {0}'.format(branch_name))


    # make sure the branch doesnt already exist on remote
    if remote_branch_exists(repo_dir, branch_name):
        msg = (
            "Error: branch {branch_name} already exists on the remote repo "
            "Please clean up that branch before proceeding\n"
            "git branch -d {branch_name}\n"
            "git push origin --delete {branch_name}\n"
            ).format(branch_name=branch_name)
        LOGGER.error(msg)
        raise RuntimeError(msg)

    # make sure repo is clean
    if has_unstaged_changes(repo_dir):
        msg = (
            "Error: Unstaged changes are present on the branch "
            "Please commit them or clean up before proceeding"
        )
        LOGGER.error(msg)
        raise RuntimeError(msg)

    main_branch = config.gitflow_branch_name()
    checkout_and_pull(repo_dir,  main_branch, pull=not opts.no_remote)

    # create release branch
    branch(repo_dir, branch_name, main_branch)

    # update cirrus conf
    config.update_package_version(new_version)
    changes = ['cirrus.conf']

    if opts.bump:
        reqs_file = os.path.join(repo_dir, 'requirements.txt')
        for pkg, version in opts.bump:
            LOGGER.info("Bumping dependency {} to {}".format(pkg, version))
            bump_package(reqs_file, pkg, version)
        changes.append(reqs_file)

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
    commit_files_optional_push(repo_dir, msg, not opts.no_remote, *changes)
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