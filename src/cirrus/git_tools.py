#!/usr/bin/env python
"""
_git_tools_

Utils for doing git and github related business

"""

import posixpath
import requests
from cirrus.configuration import get_github_auth


def get_tags_with_sha(owner, repo, token=None):
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
            "message":  commit['commit']['message']

        })

    return result




if __name__ == '__main__':
    tags = get_tags_with_sha('evansde77', 'ExampleMeddling')
    print tags
    # sha_087 = tags['0.8.7']
    # get_commit_msgs('cloudant', 'carburetor', sha_087)
    #releases = get_releases('cloudant', 'carburetor')
    #print releases