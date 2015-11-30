#!/usr/bin/env python
"""
_plusone_

repo/cirrus independent util for flagging PRs in github as plusone'd

"""
import os
import git
import sys
import json
import argparse
import requests
from configuration import get_github_auth


class GitHubHelper(object):
    """
    GitHubHelper

    Lightweight helper for this command to set up
    a GH session

    """
    def __init__(self):
        self.user, self.token = get_github_auth()
        self.auth_headers = {
            'Authorization': 'token {0}'.format(self.token),
            'Content-Type': 'application/json'
        }
        self.session = requests.Session()
        self.session.headers.update(self.auth_headers)

    def get_pr(self, org, repo, pr_id):
        """
        _get_pr_

        grab the PR details
        """
        url = "https://api.github.com/repos/{org}/{repo}/pulls/{id}".format(
            org=org,
            repo=repo,
            id=pr_id
        )
        resp = self.session.get(url)
        resp.raise_for_status()
        data = resp.json()
        return data

    def set_branch_state(self, org, repo, context, repo_dir=None, branch=None):
        """
        _current_branch_mark_status_

        Mark the CI status of the current branch.

        :param state: state of the last test run, such as "success" or "failure"
        :param context: The GH context string to use for the state, eg
           "continuous-integration/travis-ci"

        :param branch: Optional branch name or sha to set state on,
           defaults to current active branch

        """
        if repo_dir is None:
            repo_dir = os.getcwd()
        git_repo = git.Repo(repo_dir)
        if branch is None:
            branch = git_repo.active_branch.name

        # pull branch_from from remote
        ref = "refs/heads/{0}:refs/remotes/origin/{0}".format(branch)
        git_repo.remotes.origin.pull(ref)

        sha = git_repo.head.commit.hexsha
        url = "https://api.github.com/repos/{org}/{repo}/statuses/{sha}".format(
            org=org,
            repo=repo,
            sha=sha
        )
        data = json.dumps(
            {
                "state": 'success',
                "description": "State after cirrus check.",
                "context": context
            }
        )
        resp = self.session.post(url, data=data)
        resp.raise_for_status()

    def plus_one(self, org, repo, sha, context, issue_url):
        """
        _plus_one_

        Set the status for the given context to success on the
        provided sha
        """
        url = "https://api.github.com/repos/{org}/{repo}/statuses/{sha}".format(
            org=org,
            repo=repo,
            sha=sha
        )
        data = json.dumps(
            {
                "state": 'success',
                "description": "{} set to success by {}".format(
                    context, self.user
                ),
                "context": context
            }
        )
        resp = self.session.post(url, data=data)
        resp.raise_for_status()

        comment = "+1 added by {}".format(self.user)
        comment_url = "{}/comments".format(issue_url)
        comment_data = {
            "body": comment,
        }
        resp = self.session.post(comment_url, data=json.dumps(comment_data))
        resp.raise_for_status()


def build_parser():
    """
    construct a CLI parser and process args

    """
    parser = argparse.ArgumentParser(
        description='plusone command for adding +1 to a github PR'
    )

    parser.add_argument(
        '--id', '-i',
        default=None,
        type=int,
        dest='id',
        help='ID of pull request to approve/+1'
    )
    parser.add_argument(
        '--plus-one-context', '-c',
        default='+1',
        dest='plus_one_context',
        help='Github context string to use as +1 tag'
    )
    parser.add_argument(
        '--repo', '-r',
        default=None,
        dest='repo',
        help='Github Repo name'
    )
    parser.add_argument(
        '--org', '-o',
        default=None,
        dest='org',
        help='Github Organisation name'
    )
    parser.add_argument(
        '--branch', '-b',
        default=None,
        dest='branch',
        help='Branch name if not using a PR ID'
    )
    parser.add_argument(
        '--repo-dir', '-d',
        default=None,
        dest='repo_dir',
        help='Local repo path if not using a PR ID'
    )

    opts = parser.parse_args()
    return opts


def main():
    """
    _main_

    GitHub plusone tool using status and PR API

    """
    opts = build_parser()
    gh = GitHubHelper()

    if not (opts.id or opts.branch):
        print opts.id,  opts.branch
        msg = "Must supply either pull request ID or branch name"
        print msg
        sys.exit(1)

    if opts.branch is not None:
        gh.set_branch_state(
            opts.org,
            opts.repo,
            opts.plus_one_context,
            opts.repo_dir,
            branch=opts.branch
        )
    else:
        pr = gh.get_pr(opts.org, opts.repo, int(opts.id))
        sha = pr['head']['sha']
        issue_url = pr['issue_url']
        created_by = pr["user"]["login"]
        if created_by == gh.user:
            msg = "Reviewing your own Pull Requests is not allowed"
            raise RuntimeError(msg)

        gh.plus_one(opts.org, opts.repo, sha, opts.plus_one_context, issue_url)


if __name__ == '__main__':
    main()
