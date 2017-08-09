#!/usr/bin/env python
"""
_release_status_

Helper function to determine release status

"""
from cirrus.environment import repo_directory
from cirrus.github_tools import GitHubContext
from cirrus.logger import get_logger


LOGGER = get_logger()


def release_status(release):
    """
    given a release branch name or tag, look at the status
    of that release based on git history and attempt to
    check wether it has been fully merged or tagged.

    returns True if the release looks to be successfully merged and tagged

    """
    result = False
    with GitHubContext(repo_directory()) as ghc:
        LOGGER.info("Checking release status for {}".format(release))
        # work out the branch and tag for the release

        rel_pfix = ghc.config.gitflow_release_prefix()
        develop_branch = ghc.config.gitflow_branch_name()
        master_branch = ghc.config.gitflow_master_name()
        origin_name = ghc.config.gitflow_origin_name()
        if rel_pfix in release:
            release_tag = release.split(rel_pfix)[1]
            release_branch = release
        else:
            release_branch = "{}{}".format(rel_pfix, release)
            release_tag = release

        LOGGER.info("Checking: branch={} tag={}".format(release_branch, release_tag))
        branch_commit = ghc.find_release_commit(release_branch)
        tag_commit = ghc.find_release_commit(release_tag)
        LOGGER.info("Resolved Commits: branch={} tag={}".format(branch_commit, tag_commit))

        # handles caser where tag or release is not present, eg typo
        if (not tag_commit) and (not branch_commit):
            msg = (
                "Unable to find any branch or tag commits "
                "for release \'{}\'\n"
                "Are you sure this is a valid release?"
            ).format(release)
            LOGGER.error(msg)
            return False

        # check the tag commit is present on master and remote master
        tag_present = False
        if tag_commit:
            branches = ghc.commit_on_branches(tag_commit)
            remote_master = "remotes/{}/{}".format(origin_name, master_branch)
            on_master = master_branch in branches
            on_origin = remote_master in branches
            if on_master:
                LOGGER.info("Tag is present on local master {}...".format(master_branch))
                tag_present = True
            if on_origin:
                LOGGER.info("Tag is present on remote master {}...".format(remote_master))
                tag_present = True

        # look for common merge base containing the release name for master
        # and develop
        develop_merge = ghc.merge_base(release_tag, develop_branch)
        master_merge = ghc.merge_base(release_tag, master_branch)
        merge_on_develop = False
        merge_on_master = False
        if develop_merge:
            merge_on_develop = release_branch in ghc.git_show_commit(develop_merge)
        if master_merge:
            merge_on_master = release_branch in ghc.git_show_commit(master_merge)

        if merge_on_develop:
            LOGGER.info("Merge of {} is on {}".format(release_branch, develop_branch))
        else:
            LOGGER.info("Merge of {} not found on {}".format(release_branch, develop_branch))
        if merge_on_master:
            LOGGER.info("Merge of {} is on {}".format(release_branch, master_branch))
        else:
            LOGGER.info("Merge of {} not found on {}".format(release_branch, master_branch))

        if not all([tag_present, merge_on_develop, merge_on_master]):
            msg = (
                "\nRelease branch {} was not found either as a tag or merge "
                "commit on develop branch: {} or master branch: {} branches\n"
                "This may mean that the release is still running on a CI platform or "
                "has errored out. \n"
                " => Tag Present: {}\n"
                " => Merged to develop: {}\n"
                " => Merged to master: {}\n"
                "\nFor troubleshooting please see: "
                "https://github.com/evansde77/cirrus/wiki/Troubleshooting#release\n"
            ).format(
                release_branch,
                develop_branch,
                master_branch,
                tag_present,
                merge_on_develop,
                merge_on_master
            )
            LOGGER.error(msg)
            result = False
        else:
            msg = "Release {} looks to be successfully merged and tagged\n".format(release_branch)
            LOGGER.info(msg)
            result = True
    return result
