'''
Contains class for handling the creation of pull requests
'''
import json
import requests

from cirrus.configuration import get_github_auth, load_configuration
from cirrus.git_tools import get_active_branch
from cirrus.git_tools import get_tags_with_sha
from cirrus.git_tools import get_commit_msgs
from cirrus.logger import get_logger

LOGGER = get_logger()


def create_pull_request(
            repo_dir,
            pr_info,
            token=None):
    """
    Creates a pull_request on GitHub and returns the html url of the
    pull request created

    :param repo_dir: directory of git repository
    :param pr_info: dictionary containing title and body of pull request
    :param token: auth token
    """
    if repo_dir == None:
        raise RuntimeError('repo_dir is None')
    if 'title' not in pr_info:
        raise RuntimeError('title is None')
    if 'body' not in pr_info:
        raise RuntimeError('body is None')
    config = load_configuration()

    url = 'https://api.github.com/repos/{0}/{1}/pulls'.format(
        config.organisation_name(),
        config.package_name())

    if token is None:
        token = get_github_auth()[1]

    headers = {
        'Authorization': 'token {0}'.format(token),
        'Content-Type': 'application/json'}

    data = {
        'title': pr_info['title'],
        'head': get_active_branch(repo_dir).name,
        'base': config.gitflow_branch_name(),
        'body': pr_info['body']}

    resp = requests.post(url, data=json.dumps(data), headers=headers)
    if resp.status_code == 422:
        LOGGER.error(("POST to GitHub api returned {0}"
            "Have you committed your changes and pushed to remote?"
            ).format(resp.status_code))

    resp.raise_for_status()
    resp_json = resp.json()

    return resp_json['html_url']


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
