#!/usr/bin/env python
"""
_plusone_

repo/cirrus independent util for flagging PRs in github as plusone'd

"""
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
        required=True,
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
    opts = parser.parse_args()
    return opts


def main():
    """
    _main_

    GitHub plusone tool using status and PR API

    """
    opts = build_parser(sys.argv)
    gh = GitHubHelper()
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
