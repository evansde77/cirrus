'''
Contains class for handling the creation of pull requests
'''
import git
import json
import requests

from cirrus.configuration import get_github_auth, load_configuration
from cirrus.git_tools import get_active_branch
from cirrus.git_tools import get_tags_with_sha
from cirrus.git_tools import get_commit_msgs
from cirrus.git_tools import push
from cirrus.logger import get_logger


LOGGER = get_logger()


def branch_status(branch_name):
    """
    _branch_status_

    Get the branch status which should include details of CI builds/hooks etc
    See:
    https://developer.github.com/v3/repos/statuses/#get-the-combined-status-for-a-specific-ref

    returns a state which is one of 'failure', 'pending', 'success'

    """
    config = load_configuration()
    token = get_github_auth()[1]
    url = "https://api.github.com/repos/{org}/{repo}/commits/{branch}/status".format(
        org=config.organisation_name(),
        repo=config.package_name(),
        branch=branch_name
    )
    headers = {
        'Authorization': 'token {0}'.format(token),
        'Content-Type': 'application/json'
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    state = resp.json()['state']
    return state

def current_branch_mark_status(repo_dir, state):
    """
    _current_branch_mark_status_

    Mark the CI status of the current branch.

    :param repo_dir: directory of git repository
    :param state: state of the last test run, such as "success" or "failure"

    """

    LOGGER.info(u"Setting CI status for current branch to {}".format(state))

    config = load_configuration()
    token = get_github_auth()[1]
    sha = git.Repo(repo_dir).head.commit.hexsha

    try:
        # @HACK: Do a push that we expect will fail -- we just want to
        # tell the server about our sha. A more elegant solution would
        # probably be to push a detached head.
        push(repo_dir)
    except RuntimeError as ex:
        if "rejected" not in unicode(ex):
            raise

    url = "https://api.github.com/repos/{org}/{repo}/statuses/{sha}".format(
        org=config.organisation_name(),
        repo=config.package_name(),
        sha=sha
    )

    headers = {
        'Authorization': 'token {0}'.format(token),
        'Content-Type': 'application/json'
    }

    data = json.dumps(
        {
            "state": state,
            "description": "State after cirrus check.",
            # @HACK: use the travis context, which is technically
            # true, because we wait for Travis tests to pass before
            # cutting a release. In the future, we need to setup a
            # "cirrus" context, for clarity.
            "context": "continuous-integration/travis-ci"
        }
    )

    resp = requests.post(url, headers=headers, data=data)
    resp.raise_for_status()

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


def comment_on_sha(owner, repo, comment, sha, path, token=None):
    """
    add a comment to the commit/sha provided
    """
    url = "https://api.github.com/repos/{owner}/{repo}/commits/{sha}/comments".format(
        owner=owner, repo=repo, sha=sha
    )
    if token is None:
        token = get_github_auth()[1]

    headers = {
        'Authorization': 'token {}'.format(token),
        'Content-Type': 'application/json'
    }
    payload = {
        "body": comment,
        "path": path,
        "position": 0,
    }
    resp = requests.get(url, headers=headers, data=payload)
    resp.raise_for_status()


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
