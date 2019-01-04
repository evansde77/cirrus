import os

from cirrus.configuration import load_configuration
from cirrus.github_tools import GitHubContext
from cirrus.release.utils import release_branch_name, release_config, is_nightly, remove_nightly
from cirrus.logger import get_logger

LOGGER = get_logger()

def cleanup_release(opts):
    """
    _cleanup_release_

    Remove local and remote release branches if they exist

    """
    config = load_configuration()
    repo_dir = os.getcwd()
    pfix = config.gitflow_release_prefix()
    branch_name = release_branch_name(config)

    if opts.version is not None:
        if not opts.version.startswith(pfix):
            branch_name = "{0}{1}".format(
                pfix,
                opts.version
            )
        else:
            branch_name = opts.version
    LOGGER.info("Cleaning release branches for {}".format(branch_name))
    with GitHubContext(repo_dir) as ghc:
        ghc.delete_branch(branch_name, not opts.no_remote)


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
                u"Not on the expected release branch according "
                u"to cirrus.conf\n Expected:{0} but on {1}"
            ).format(expected_branch, release_branch)
            LOGGER.error(msg)
            raise RuntimeError(msg)

        # merge release branch into master
        LOGGER.info(u"Tagging and pushing {0}".format(tag))
        if opts.skip_master:
            LOGGER.info(u'Skipping merging to {}'.format(master))
        if opts.skip_develop:
            LOGGER.info(u'Skipping merging to {}'.format(develop))

        if opts.log_status:
            ghc.log_branch_status(master)
        if not opts.skip_master:
            sha = ghc.repo.head.ref.commit.hexsha

            if rel_conf['wait_on_ci']:
                #
                # wait on release branch CI success
                #
                LOGGER.info(u"Waiting on CI build for {0}".format(release_branch))
                ghc.wait_on_gh_status(
                    sha,
                    timeout=rel_conf['wait_on_ci_timeout'],
                    interval=rel_conf['wait_on_ci_interval']
                )

            LOGGER.info(u"Merging {} into {}".format(release_branch, master))
            ghc.pull_branch(master, remote=not opts.no_remote)
            ghc.merge_branch(release_branch)
            sha = ghc.repo.head.ref.commit.hexsha


            if rel_conf['wait_on_ci_master']:
                #
                # wait on release branch CI success
                #
                LOGGER.info(u"Waiting on CI build for {0}".format(master))
                ghc.wait_on_gh_status(
                    sha,
                    timeout=rel_conf['wait_on_ci_timeout'],
                    interval=rel_conf['wait_on_ci_interval']
                )
            if rel_conf['update_github_context']:
                for ctx in rel_conf['github_context_string']:
                    LOGGER.info(u"Setting {} for {}".format(
                        ctx,
                        sha)
                    )
                    ghc.set_branch_state(
                        'success',
                        ctx,
                        branch=sha
                    )

            if rel_conf['update_master_github_context']:
                for ctx in rel_conf['github_master_context_string']:
                    LOGGER.info(u"Setting {} for {}".format(
                        ctx,
                        sha)
                    )
                    ghc.set_branch_state(
                        'success',
                        ctx,
                        branch=sha
                    )
            if not opts.no_remote:
                ghc.push_branch_with_retry(
                    attempts=rel_conf['push_retry_attempts'],
                    cooloff=rel_conf['push_retry_cooloff']
                )
                LOGGER.info(u"Tagging {} as {}".format(master, tag))
            ghc.tag_release(
                tag,
                master,
                push=not opts.no_remote,
                attempts=rel_conf['push_retry_attempts'],
                cooloff=rel_conf['push_retry_cooloff']
            )

        LOGGER.info(u"Merging {} into {}".format(release_branch, develop))
        if opts.log_status:
            ghc.log_branch_status(develop)
        if not opts.skip_develop:
            ghc.pull_branch(develop, remote=not opts.no_remote)
            ghc.merge_branch(release_branch)
            if is_nightly(tag):
                remove_nightly(ghc)
            sha = ghc.repo.head.ref.commit.hexsha

            if rel_conf['wait_on_ci_develop']:
                #
                # wait on release branch CI success
                #
                LOGGER.info(u"Waiting on CI build for {0}".format(develop))
                ghc.wait_on_gh_status(
                    sha,
                    timeout=rel_conf['wait_on_ci_timeout'],
                    interval=rel_conf['wait_on_ci_interval']
                )
            if rel_conf['update_github_context']:
                for ctx in rel_conf['github_context_string']:
                    LOGGER.info(u"Setting {} for {}".format(
                        ctx,
                        sha)
                    )
                    ghc.set_branch_state(
                        'success',
                        ctx,
                        branch=sha
                    )

            if rel_conf['update_develop_github_context']:
                for ctx in rel_conf['github_develop_context_string']:
                    LOGGER.info(u"Setting {} for {}".format(
                        ctx,
                        sha)
                    )
                    ghc.set_branch_state(
                        'success',
                        ctx,
                        branch=sha
                    )
            if not opts.no_remote:
                ghc.push_branch_with_retry(
                    attempts=rel_conf['push_retry_attempts'],
                    cooloff=rel_conf['push_retry_cooloff']
                )
        if opts.cleanup:
            ghc.delete_branch(release_branch, remote=not opts.no_remote)