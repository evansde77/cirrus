'''
Contains class for handling the creation of pull requests
'''
import os
import git
import json
import time
import arrow
import requests
import itertools

from cirrus.configuration import get_github_auth, load_configuration
from cirrus.git_tools import get_active_branch
from cirrus.git_tools import push
from cirrus.logger import get_logger


LOGGER = get_logger()


class GitHubContext(object):
    """
    _GitHubContext_

    Util that establishes a GH session and pulls together
    useful GH commands

    """
    def __init__(self, repo_dir, package_dir=None):
        self.repo_dir = repo_dir
        self.repo = git.Repo(repo_dir)
        self.config = load_configuration(package_dir)
        self.gh_user, self.token = get_github_auth()
        self.auth_headers = {
            'Authorization': 'token {0}'.format(self.token),
            'Content-Type': 'application/json'
        }

    @property
    def active_branch_name(self):
        """return the current branch name"""
        return self.repo.active_branch.name

    def __enter__(self):
        """start context, establish session"""
        self.session = requests.Session()
        self.session.headers.update(self.auth_headers)
        return self

    def __exit__(self, *args):
        pass

    def branch_state(self, branch=None):
        """
        _branch_state_

        Get the branch status which should include details of CI builds/hooks etc
        See:
        https://developer.github.com/v3/repos/statuses/#get-the-combined-status-for-a-specific-ref

        returns a state which is one of 'failure', 'pending', 'success'

        """
        if branch is None:
            branch = self.active_branch_name
        url = "https://api.github.com/repos/{org}/{repo}/commits/{branch}/status".format(
            org=self.config.organisation_name(),
            repo=self.config.package_name(),
            branch=branch
        )
        resp = self.session.get(url)
        resp.raise_for_status()
        state = resp.json()['state']
        return state

    def branch_status_list(self, branch):
        """
        Detailed list of status information for the
        given branch

        """
        url = "https://api.github.com/repos/{org}/{repo}/commits/{branch}/statuses".format(
            org=self.config.organisation_name(),
            repo=self.config.package_name(),
            branch=branch
        )
        resp = self.session.get(url)
        resp.raise_for_status()
        data = resp.json()
        for d in data:
            yield d

    def log_branch_status(self, branch):
        """
        _log_branch_status_

        Log all the current status checks for the named
        branch
        """
        for x in self.branch_status_list(branch):
            update_time = arrow.get(x['updated_at']).humanize()
            context = x['context']
            user = x['creator']['login']
            state = x['state']
            msg = (
                "Branch {branch} Check {context} is {state}, "
                "created by {user} and updated {update}"
            ).format(
                branch=branch, context=context, user=user,
                state=state, update=update_time
            )
            LOGGER.info(msg)

    def set_branch_state(self, state, context, branch=None):
        """
        _current_branch_mark_status_

        Mark the CI status of the current branch.

        :param state: state of the last test run, such as "success" or "failure"
        :param context: The GH context string to use for the state, eg
           "continuous-integration/travis-ci"

        :param branch: Optional branch name or sha to set state on,
           defaults to current active branch

        """
        if branch is None:
            branch = self.repo.active_branch.name

        LOGGER.info(u"Setting CI status for branch {} to {}".format(branch, state))

        sha = self.repo.head.commit.hexsha

        try:
            # @HACK: Do a push that we expect will fail -- we just want to
            # tell the server about our sha. A more elegant solution would
            # probably be to push a detached head.
            push(self.repo_dir)
        except RuntimeError as ex:
            if "rejected" not in unicode(ex):
                raise

        url = "https://api.github.com/repos/{org}/{repo}/statuses/{sha}".format(
            org=self.config.organisation_name(),
            repo=self.config.package_name(),
            sha=sha
        )
        data = json.dumps(
            {
                "state": state,
                "description": "State after cirrus check.",
                "context": context
            }
        )
        resp = self.session.post(url, data=data)
        resp.raise_for_status()

    def wait_on_gh_status(self, branch_name=None, timeout=600, interval=2):
        """
        _wait_on_gh_status_

        Wait for CI checks to complete for the branch named

        :param branch_name: name of branch to watch
        :param timeout: max wait time in seconds
        :param interval: pause between checks interval in seconds

        """
        if branch_name is None:
            branch_name = self.active_branch_name

        time_spent = 0
        status = self.branch_state(branch_name)
        LOGGER.info("Waiting on CI status of {}...".format(branch_name))
        while status == 'pending':
            if time_spent > timeout:
                LOGGER.error("Exceeded timeout for branch status {}".format(branch_name))
                break
            status = branch_status(branch_name)
            time.sleep(interval)
            time_spent += interval

        if status != 'success':
            msg = "CI Test status is not success: {} is {}".format(branch_name, status)
            LOGGER.error(msg)
            raise RuntimeError(msg)

    def pull_branch(self, branch_name=None):
        """
        _pull_branch_

        Pull the named branch from origin, if it isnt
        the current active branch, it will be checked out
        """
        if branch_name is not None:
            self.repo.git.checkout(branch_name)
        ref = "refs/heads/{0}:refs/remotes/origin/{0}".format(branch_name)
        return self.repo.remotes.origin.pull(ref)

    def push_branch(self, branch_name=None):
        """
        _push_branch_

        Push the named branch to remote, if branch_name isnt provided
        the current active branch is pushed
        """
        if branch_name is not None:
            self.repo.git.checkout(branch_name)
        ret = self.repo.remotes.origin.push(self.repo.head)
        # Check to make sure that we haven't errored out.
        for r in ret:
            if r.flags >= r.ERROR:
                raise RuntimeError(unicode(r.summary))
        return ret

    def push_branch_with_retry(self, branch_name=None, attempts=300, cooloff=2):
        """
        _push_branch_with_retry_

        Work around intermittent push failures with a dumb exception retry loop

        """
        count = 0
        error_flag = None
        while count < attempts:
            try:
                error_flag = None
                self.push_branch(branch_name=branch_name)
                break
            except RuntimeError as ex:
                msg = "Error pushing branch {}: {}".format(branch_name, str(ex))
                LOGGER.info(msg)
                count += 1
                error_flag = ex
                time.sleep(cooloff)
        if error_flag is not None:
            msg = "Unable to push branch {} due to repeated failures: {}".format(
                self.active_branch_name, str(ex)
            )
            raise RuntimeError(msg)

    def merge_branch(self, branch_name):
        """
        _merge_branch_

        merge branch_name into current branch using no-ff option
        """
        result = self.repo.git.merge('--no-ff', branch_name)
        return result

    def tag_release(self, tag, master='master', push=True, attempts=1, cooloff=2):
        """
        _tag_release_

        Tag the release on the master branch and, if push is True
        push the tag to the remote
        """
        if self.active_branch_name != master:
            self.repo.git.checkout(master)

        exists = any(existing_tag.name == tag for existing_tag in self.repo.tags)
        if exists:
            # tag already exists
            msg = (
                "Attempting to create tag {0} on "
                "{1} but tag exists already"
            ).format(tag, master)
            raise RuntimeError(msg)
        self.repo.create_tag(tag)
        if push:
            count = 0
            error_flag = None
            while count < attempts:
                error_flag = None
                try:
                    self.repo.remotes.origin.push(self.repo.head, tags=True)
                    break
                except Exception as ex:
                    msg = "Error pushing tags: {}".format(ex)
                    LOGGER.warning(msg)
                    error_flag = ex
                    time.sleep(cooloff)
                count += 1
            if error_flag is not None:
                msg = "Unable to push tags {} due to repeated failures: {}".format(
                    tag, str(ex)
                )
                raise RuntimeError(msg)


    def delete_branch(self, branch_name, remote=True):
        """
        _delete_branch_

        Delete the local and (if remote is True) branch
        """
        if self.active_branch_name == branch_name:
            msg = "Cant delete branch {} because it is active".format(branch_name)
            raise RuntimeError(msg)
        self.repo.git.branch('-D', branch_name)
        if remote:
            self.repo.git.push('origin', '--delete', branch_name)

    def iter_github_branches(self):
        """
        iterate over branch names using the GH API.

        Warning: This is subject to rate limiting
        for repos with lots of branches

        """
        url = "https://api.github.com/repos/{org}/{repo}/branches".format(
            org=self.config.organisation_name(),
            repo=self.config.package_name()
        )
        params = {'per_page': 100}
        resp = self.session.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        for row in data:
            yield row['name']
        next_page = resp.links.get('next')
        while next_page is not None:
            resp = self.session.get(next_page['url'], params=params)
            resp.raise_for_status()
            data = resp.json()
            for row in data:
                yield row['name']
            next_page = resp.links.get('next')

    def iter_git_branches(self, merged=False):
        """
        iterate over all git branches, remote and local,
        using git branch -a.

        Optionally filter for only branches that have been merged
        using passing merged=True

        """
        args = ['-a']
        if not merged:
            args.append('--no-merged')
        branch_data = self.repo.git.branch(*args)
        branches = (x.strip() for x in branch_data.split() if x.strip())
        for b in branches:
            yield b

    def iter_git_feature_branches(self, merged=False):
        """
        iterate over unmerged feature branches
        using the branch prefix to find feature branches

        toggle the merged boolean to include previously merged branches

        """
        feature_pfix = "remotes/origin/{}".format(self.config.gitflow_feature_prefix())
        branches = self.iter_git_branches(merged)
        branches = itertools.ifilter(lambda x: x.startswith(feature_pfix), branches)
        return branches

    def pull_requests(self, user=None):
        """
        _pull_requests_

        Iterate over the open pull requests for this repo,
        optionally filtering by username

        :param user: GH username to filter on
        :returns: yields json structures for each matched PR

        """
        url = "https://api.github.com/repos/{org}/{repo}/pulls".format(
            org=self.config.organisation_name(),
            repo=self.config.package_name()
        )
        params = {
            'state': 'open',
        }

        resp = self.session.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        gen = iter(data)
        if user:
            gen = itertools.ifilter(lambda x: x['user']['login'] == user, gen)
        for row in gen:
            yield row

    def pull_request_details(self, pr):
        """
        _pull_request_details_

        Get the json data for an individual pr, specified by the
        provided PR id

        :param pr: int, id of pull request
        :returns: json structure (see GH API)

        """
        url = "https://api.github.com/repos/{org}/{repo}/pulls/{number}".format(
            org=self.config.organisation_name(),
            repo=self.config.package_name(),
            number=pr
        )

        resp = self.session.get(url)
        resp.raise_for_status()
        data = resp.json()
        return data

    def plus_one_pull_request(self, pr_id=None, pr_data=None, context='+1'):
        """
        _plus_one_pull_request_

        """
        if pr_data is None:
            pr_data = self.pull_request_details(pr_id)

        pr_status_url = pr_data["statuses_url"]
        created_by = pr_data["user"]["login"]
        if created_by == self.gh_user:
            msg = "Reviewing your own Pull Requests is not allowed"
            raise RuntimeError(msg)

        status = {
            'state': 'success',
            'description': 'Reviewed by {0}'.format(self.gh_user),
            'context': context,
        }
        resp = self.session.post(pr_status_url, data=json.dumps(status))
        resp.raise_for_status()

    def review_pull_request(
            self,
            pr,
            comment,
            plusone=False,
            plusonecontext='+1'):
        """
        _review_pull_request_

        Add a comment to the numbered PR and optionally set the
        +1 status context for it

        """
        pr_data = self.pull_request_details(pr)
        comment_url = "{}/comments".format(pr_data['issue_url'])

        comment_data = {
            "body": comment,
        }
        resp = self.session.post(comment_url, data=json.dumps(comment_data))
        resp.raise_for_status()
        if plusone:
            self.plus_one_pull_request(pr_data=pr_data, context=plusonecontext)


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
    if repo_dir is None:
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
        LOGGER.error(
            (
                "POST to GitHub api returned {0}"
                "Have you committed your changes and pushed to remote?"
            ).format(resp.status_code)
        )

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

    releases = [release for release in resp.json()]
    return releases
