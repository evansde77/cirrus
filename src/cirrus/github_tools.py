'''
Contains class for handling the creation of pull requests
'''
import itertools
import json
import requests

from cirrus.configuration import get_github_auth, load_configuration
from cirrus.git_tools import get_active_branch


def create_pull_request(
            repo_dir,
            owner,
            pr_info,
            token=None):
    """
    Creates a pull_request on GitHub

    :param repo_dir: directory of git repository
    :param pr_info: dictionary containing title and body of pull request
    :param owner: GitHub owner
    :param token: auth token
    """
    if repo_dir == None:
        raise RuntimeError('repo_dir is None')
    if owner == None:
        raise RuntimeError('owner is None')
    if 'title' not in pr_info:
        raise RuntimeError('title is None')
    if 'body' not in pr_info:
        raise RuntimeError('body is None')
    config = load_configuration

    url = 'https://api.github.com/repos/{0}/{1}/pulls'.format(
        owner,
        repo_dir)

    if token is None:
        token = get_github_auth()[1]

    headers = {
        'Authorization': 'token {0}'.format(token),
        'Content-Type': 'application/json'}

    data = {
        'title': pr_info['title'],
        'head': get_active_branch(repo_dir),
        'base': config.gitflow_branch_name(),
        'body': pr_info['body']}

    resp = requests.post(url, data=json.dumps(data), headers=headers)
    resp.rais_for_status()


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
