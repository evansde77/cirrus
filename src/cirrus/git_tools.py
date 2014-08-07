#!/usr/bin/env python
"""
_git_tools_

Utils for doing git and github related business

"""
import git
import itertools
import posixpath
import requests

from cirrus.configuration import get_github_auth


def checkout_and_pull(repo_dir, branch_from):
    """
    _checkout_and_pull_

    Checkout a branch (branch_from) from a git repo (repo_dir)
    and then pull updates from origin

    returns a reference to the pulled branch
    """
    repo = git.Repo(repo_dir)

    if repo.active_branch != branch_from:
        dev_branch = getattr(repo.heads, branch_from)
        dev_branch.checkout()

    # pull branch_from from remote
    ref = "refs/heads/{0}:refs/remotes/origin/{0}".format(branch_from)
    return repo.remotes.origin.pull(ref)


def branch(repo_dir, branchname, branch_from):
    """
    _git_branch_

    Create a new branch off of branch_from, from repo, named
    branchname
    """
    repo = git.Repo(repo_dir)

    if branchname in repo.heads:
        msg = "Branch: {0} already exists.".format(branchname)
        print "{0} Checking it out...".format(msg)
        branch_ref = getattr(repo.heads, branchname)
        branch_ref.checkout()
    else:
        g = git.Git(repo_dir)
        g.checkout(branch_from, b=branchname)

    if not str(repo.active_branch) == branchname:
        msg = "uh oh, not on expected branch"
        raise RuntimeError((
            "{0}. You are here -> {1}, "
            "you expected to be here -> {2}"
            ).format(msg, repo.active_branch, branchname))


def commit_files(repo_dir, commit_msg, *filenames):
    """
    _commit_files_

    Add the list of filenames and commit them with the message provided
    to the current branch in the repo specified.
    Pushes changes to remote branch after commit

    """
    repo = git.Repo(repo_dir)
    repo.index.add(filenames)

    # commits with message
    new_commit = repo.index.commit(commit_msg)
    # push branch to origin
    result = repo.remotes.origin.push(repo.head)
    return result
