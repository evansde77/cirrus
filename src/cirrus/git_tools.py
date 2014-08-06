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
        print "***active_branch: {0}, branch_from: {1}".format(repo.active_branch, branch_from)
        print "***heads: {0}".format(repo.heads)
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
        print "{0} /n checking it out...".format(msg)
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


def get_tags_with_sha(owner, repo, token=None):
    """
    _get_tags_with_sha_

    Get list of tags for a repo and return a map of
    tag:sha

    """
    url = "https://api.github.com/repos/{owner}/{repo}/tags".format(
        owner=owner, repo=repo
    )
    if token is None:
        token = get_github_auth()[1]

    headers = {
        'Authorization': 'token %s' % token
    }

    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    result = { r['name']:r['commit']['sha'] for r in resp.json()}
    return result


def get_tags(owner, repo, token=None):
    """
    _get_tags_

    returns a list of tags for the given repo, ordered as
    newest first

    """
    tags_with_sha = get_tags_with_sha(owner, repo, token)
    tags = tags_with_sha.keys()
    tags.sort(reverse=True)
    return tags


def create_tag(owner, repo, tag, message, sha, token=None):
    """
    _create_tag_

    Create a new tag for the package
    """


def create_release(owner, repo, tag, token=None):
    """
    _create_release_

    Create a new release from the provided tag

    """


def get_releases(owner, repo, token=None):

    url = "https://api.github.com/repos/{owner}/{repo}/releases".format(
        owner=owner, repo=repo
    )
    if token is None:
        token = get_github_auth()[1]

    headers = {
        'Authorization': 'token %s' % token
    }

    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    releases = [ release for release in resp.json() ]
    return releases


def get_commit_msgs(owner, repo, since_sha, token=None):
    """
    _get_commit_msgs_

    Get commit message data for the repo provided since the
    since_sha value of a commit or tag.

    """
    url = "https://api.github.com/repos/{owner}/{repo}/commits".format(
        owner=owner, repo=repo
    )

    params = {'sha': since_sha}
    if token is None:
        token = get_github_auth()[1]

    headers = {
        'Authorization': 'token %s' % token
    }

    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    result = []
    for commit in resp.json():
        result.append({
            "committer" : commit['committer']['login'],
            "message":  commit['commit']['message'],
            "date" : commit['commit']['committer']['date']

        })
    return result


def format_commit_messages(rows):
    """
    _format_commit_messages_

    Consume the data produced by get_commit_msgs and
    generate a set of release notes, broken down by author

    Output looks like:

    - Commit History:
    -- Author: GITHUBUSERNAME
    --- DATETIME: COMMIT MESSAGE

    """

    result = [" - Commit History:"]

    for author, commits in itertools.groupby(rows, lambda x: x['committer']):
        result.append(" -- Author: {0}".format(author))
        sorted_commits = sorted([ c for c in commits ], key=lambda x: x['date'], reverse=True)
        result.extend( ' --- {0}: {1}'.format(commit['date'],commit['message']) for commit in sorted_commits)

    return '\n'.join(result)


def build_release_notes(org, repo, since_tag):
    """
    Given an org, repo and tag, generate release notes for all
    commits since that tag

    """
    tags = get_tags_with_sha(org, repo)
    if since_tag not in tags:
        msg = "Could not find tag {0} in {1}/{2}".format(since_tag, org, repo)
        raise RuntimeError(msg)

    sha = tags[since_tag]
    msgs = get_commit_msgs(org, repo, sha)
    rel_notes = format_commit_messages(msgs)
    return rel_notes

