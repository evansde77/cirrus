#!/usr/bin/env python
"""
_git_tools_

Utils for doing git and github related business

"""
import git


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


def push(repo_dir):
    """
    _push_

    Push local branch to remote
    """
    repo = git.Repo(repo_dir)
    return repo.remotes.origin.push(repo.head)


def tag_release(repo_dir, tag, master='master'):
    """
    _tag_release_

    Checkout master, tag it and push tags

    """
    checkout_and_pull(repo_dir, master)
    repo = git.Repo('.')
    exists = any(existing_tag.name == tag for existing_tag in repo.tags)
    if exists:
        # tag already exists
        msg = (
            "Attempting to create tag {0} on "
            "{1} but tag exists already"
        ).format(tag, master)
        raise RuntimeError(msg)
    repo.create_tag(tag)
    repo.remotes.origin.push(repo.head, tags=True)


def get_active_branch(repo_dir):
    """
    _active_branch_

    Returns active branch for a give directory
    """
    repo = git.Repo(repo_dir)
    return repo.active_branch


def merge(repo_dir, source, destination):
    """
    _merge_

    Merge source branch into destination branch
    """
    repo = git.Repo(repo_dir)
    repo.git.checkout(source)

    ref = "refs/heads/{0}:refs/remotes/origin/{0}".format(source)
    repo.remotes.origin.pull(ref)

    repo.git.merge(destination)
