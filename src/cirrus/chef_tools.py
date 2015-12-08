#!/usr/bin/env python
"""
_chef_tools_

Helpers/utils for modifying chef objects on the server and in a local repo

"""
import os
import git
import json
import chef
import uuid

from contextlib import contextmanager
from cirrus.logger import get_logger

LOGGER = get_logger()


short_uuid = lambda: str(uuid.uuid4()).rsplit('-', 1)[1]


def get_dotted(d, key):
    """
    _get_dotted_

    take an element1.element2.element3 style string
    and look up the nested element from the given dictionary,
    returning the value. Will raise KeyError if it isnt found

    """
    value = d
    for k in key.split('.'):
        if not isinstance(value, dict):
            raise KeyError(key)
        value = value[k]
    return value


def set_dotted(d, key, value):
    """
    _set_dotted_

    support setting a value where the key is a . delimited
    string representing the nested key

    """
    dest = d
    keys = key.split('.')
    last_key = keys.pop()
    for k in keys:
        if k not in dest:
            dest[k] = {}
        dest = dest[k]
        if not isinstance(dest, dict):
            raise TypeError('non-dict element in key {0} at {1}'.format(key, k))
    dest[last_key] = value


def edit_chef_environment(server_url, cert, username, environment, attributes):
    """
    _edit_chef_environment_

    For a given chef server, edit the override attributes in the named
    environment making changes for each dotted key:value pair in attributes

    Eg:

    attributes = {
        'application.app_version': 'x.y.z',
        'application.some_url': 'http://www.google.com'
    }
    will result in changes:
      env.override_attributes['application']['app_version'] = 'x.y.z'
      env.override_attributes['application']['some_url'] = 'http://www.google.com'

    :param server_url: URL of your chef server
    :param cert: Client.pem file location
    :param username: Chef username matching the cert
    :param environment: name of chef environment eg 'production'
    :param attributes: dict of dotted attribute key value pairs to change
      in the env

    """
    with chef.ChefAPI(server_url, cert, username):
        env = chef.Environment(environment)
        overrides = env.override_attributes
        LOGGER.info("Editing Chef Server Environment: {} as {}".format(environment, username))
        for attr, new_value in attributes.iteritems():
            LOGGER.info(" => Setting {}={}".format(attr, new_value))
            set_dotted(overrides, attr, new_value)
        env.save()


def edit_chef_role(server_url, cert, username, rolename, attributes):
    """
    _edit_chef_role_

    For a given chef server, edit the override attributes in the named role
    making changes for each dotted key:value pair in attributes.

    """
    with chef.ChefAPI(server_url, cert, username):
        role = chef.Role(rolename)
        LOGGER.info("Editing Chef Server Role: {} as {}".format(rolename, username))
        overrides = role.override_attributes
        for attr, new_value in attributes.iteritems():
            LOGGER.info(" => Setting {}={}".format(attr, new_value))
            set_dotted(overrides, attr, new_value)
        role.save()


def list_nodes(server_url, cert, username, query, attribute='name', format_str=None):
    """
    _list_nodes_

    Get a list of chef nodes using a chef node seach query.
    Use attribute to select the attribute from the matching nodes
    and optionally provide a format string to drop the result into
    to create well formatted node names

    Example:
    list_nodes(server_url , cert, 'server_user',
        "role:some_role AND environment:prod",
        attribute='automatic.ip.public'
    )

    Will list all nodes with some_role in the prod environment
      and return the node['automatic']['ip']['public'] attribute for each node

    list_nodes(server_url, cert, 'server_url',
        "role:some_role AND environment:prod",
        attribute='name', format_str='{}.cloudant.com')

    Will extract the name attribute for each node and return that value expanded
    in the format_str

    :param server_url: Chef Server URL
    :param cert: path to PEM cert for chef server auth
    :param username: Chef Server username
    :param query: chef node search query string
    :param attribute: Attribute name to be extracted from node data,
       can be a dot.delimited.style name
    :param format_str: optional format string to apply to each result
      for each node.

    """
    result = []
    with chef.ChefAPI(server_url, cert, username):
        for row in chef.search.Search('node', query):
            attr = get_dotted(row, attribute)
            if format_str is not None:
                attr = format_str.format(attr)
            result.append(attr)
            LOGGER.info("Node Found:{}".format(attr))
    return result


def update_chef_environment(server_url, cert, username, environment, attributes, chef_repo=None, **kwargs):
    """
    _update_chef_environment_

    Update chef environment on server and also in chef repo if provided

    """
    #
    # update chef_repo
    #
    if chef_repo is not None:
        LOGGER.info("Updating chef repo: {}".format(chef_repo))
        if not os.path.exists(chef_repo):
            msg = (
                "chef_repo not found: {} please clone to a "
                "valid path"
            ).format(chef_repo)
            LOGGER.error(msg)
            raise RuntimeError(msg)
        r = ChefRepo(chef_repo)
        feature_name = kwargs.get(
            "feature_name", "cirrus_{}_{}".format(
                environment, short_uuid()
            )
        )
        if environment not in r.environments():
            msg = (
                "Unable to find environment {} in repo {} "
                "Known Environments are: {}"
            ).format(environment, chef_repo, r.environments())
            LOGGER.error(msg)
            raise RuntimeError(msg)
        with r.feature_branch(feature_name, push=kwargs.get('push', False)):
            with r.edit_environment(environment, branch=r.current_branch_name) as env:
                LOGGER.info("Updating Chef Environment: {}".format(environment))
                for x, y in attributes.iteritems():
                    LOGGER.info(" => Setting {}={}".format(x, y))
                    set_dotted(env['override_attributes'], x, y)

    #
    # update chef server
    #
    edit_chef_environment(server_url, cert, username, environment, attributes)


class ChefRepo(object):
    """
    _ChefRepo_

    Wrapper for a git chef-repo to assist in
    editing and committing changes to json files such as
    environments and roles.

    Provides contexts for editing envs etc and saving and
    committing the changes.

    Eg:

    c = ChefRepo('./chef-repo')
    with c.edit_environment('production') as env:
        env['override_attributes']['thing'] = 'X.Y.Z'

    """
    def __init__(self, repo_dir, **options):
        self.repo_dir = repo_dir
        self.repo = git.Repo(repo_dir)
        self.git_api = git.Git(repo_dir)
        self.envs = options.get('environments_dir', 'environments')
        self.roles_dir = options.get('roles_dir', 'roles')

    @property
    def current_branch_name(self):
        return str(self.repo.active_branch)

    def checkout_and_pull(self, branch_name='master'):
        """
        _checkout_and_pull_

        Check out the specified branch, git pull it

        """
        if self.repo.active_branch != branch_name:
            dev_branch = getattr(self.repo.heads, branch_name)
            dev_branch.checkout()

        # pull branch_name from remote
        ref = "refs/heads/{0}:refs/remotes/origin/{0}".format(branch_name)
        return self.repo.remotes.origin.pull(ref)

    def commit_files(self, commit_msg, *filenames):
        """
        _commit_files_

        Add the list of filenames and commit them with the message provided
        to the current branch in the repo specified.
        Pushes changes to remote branch after commit

        """
        self.repo.index.add(filenames)
        # commits with message
        self.repo.index.commit(commit_msg)
        # push branch to origin
        result = self.repo.remotes.origin.push(self.repo.head)
        return result

    def _read_json_file(self, dirname, filename):
        """
        util to read json file in repo.
        appends .json to filename if not present
        """
        if not filename.endswith('.json'):
            filename = '{0}.json'.format(filename)
        j_file = os.path.join(self.repo_dir, dirname, filename)
        if not os.path.exists(j_file):
            raise RuntimeError("Could not read json file: {0}".format(j_file))

        with open(j_file, 'r') as handle:
            data = json.load(handle)
        return data

    def _write_json_file(self, dirname, filename, data):
        """
        util to write and pprint json file, return path to edited file

        """
        if not filename.endswith('.json'):
            filename = '{0}.json'.format(filename)
        j_file = os.path.join(self.repo_dir, dirname, filename)
        with open(j_file, 'w') as handle:
            json.dump(data, handle, indent=2)
        return j_file

    def environments(self):
        """
        _environments_

        list environments in the repo

        """
        envs_dir = os.path.join(self.repo_dir, self.envs)
        result = []
        for f in os.listdir(envs_dir):
            if f.endswith('.json'):
                result.append(f.replace('.json', ''))
        return result

    def get_environment(self, env_name):
        """
        _get_environment_

        Get the named environment as a dictionary structure
        returns None if not found
        """
        if env_name not in self.environments():
            return None
        return self._read_json_file(self.envs, env_name)

    def save_environment(self, env_name, env_data):
        """
        _save_environment_

        Write formatted json to file
        """
        self._write_json_file(self.envs, env_name, env_data)
        return '{0}/{1}.json'.format(self.envs, env_name)

    @contextmanager
    def edit_environment(self, environment, branch=None, message=None):
        """
        context manager that allows you to edit,
        save and commit an environment

        """
        if branch is not None:
            if self.repo.active_branch != branch:
                dev_branch = getattr(self.repo.heads, branch)
                dev_branch.checkout()

        if message is None:
            message = "cirrus.ChefRepo.edit_environment({0}, {1})".format(
                environment, branch
            )
        env = self.get_environment(environment)
        yield env
        edited = self.save_environment(environment, env)
        self.commit_files(message, edited)

    def roles(self):
        """
        _roles_

        list roles in the repo

        """
        result = []
        roles_dir = os.path.join(self.repo_dir, self.roles_dir)
        for f in os.listdir(roles_dir):
            if f.endswith('.json'):
                result.append(f.replace('.json', ''))
        return result

    def get_role(self, role):
        """
        _get_role_

        Get the dictionary for the named role or None if not found
        """
        if role not in self.roles():
            return None
        return self._read_json_file(self.roles_dir, role)

    def save_role(self, role, role_data):
        """
        _save_role_

        Write formatted json to file
        """
        self._write_json_file(self.roles_dir, role, role_data)
        return '{0}/{1}.json'.format(self.roles_dir, role)

    @contextmanager
    def edit_role(self, role, branch='master', message=None):
        """
        context manager that allows you to edit,
        save and commit an role

        """
        self.checkout_and_pull(branch)
        if message is None:
            message = "cirrus.ChefRepo.edit_role({0}, {1})".format(
                role, branch
            )
        data = self.get_role(role)
        yield data
        edited = self.save_role(role, data)
        self.commit_files(message, edited)

    def _start_feature_branch(self, feature_branch, base_branch='master'):
        """
        _start_feature_branch_

        Start a new feature  branch using the branch name provided off the
        specified base branch.
        Will checkout and set as current branch

        For use within feature_branch context

        """
        if str(self.repo.active_branch) != base_branch:
            self.checkout_and_pull(base_branch)

        if feature_branch in self.repo.heads:
            msg = "Error: feature branch: {0} already exists.".format(feature_branch)
            LOGGER.error(msg)
            raise RuntimeError(msg)

        self.git_api.checkout(base_branch, b=feature_branch)
        LOGGER.info("On Feature Branch: {}".format(self.repo.active_branch))

    def _finish_feature_branch(
            self,
            feature_branch,
            base_branch='master',
            push_feature=True,
            merge=True,
            push=True):
        """
        _finish_feature_branch_

        Complete work on the named feature branch and merge it back into
        the head of the base branch. If push is True, push those changes
        to the origin

        For use within feature_branch content

        """
        if str(self.repo.active_branch) != feature_branch:
            msg = "Not on expected feature branch: {}".format(feature_branch)
            raise RuntimeError(msg)

        if push_feature:
            self.repo.remotes.origin.push(self.repo.head)

        if merge:
            self.repo.git.checkout(base_branch)
            ref = "refs/heads/{0}:refs/remotes/origin/{0}".format(base_branch)
            self.repo.remotes.origin.pull(ref)
            self.repo.git.merge(feature_branch)
            LOGGER.info(
                "Merging Feature Branch {} into {}".format(
                    feature_branch, self.repo.active_branch
                )
            )

            # push base branch to origin
            if push:
                self.repo.remotes.origin.push(self.repo.head)

    @contextmanager
    def feature_branch(self, feature_name, base_branch='master', push=True):
        """
        _feature_branch_

        Start and merge edits on a feature branch.
        Will create a new branch called "feature/<feature_name>" off the
        specified base branch, allow you to make changes in the repo
        and then merges that branch back into the base branch and optionally
        push the changes to the remote

        """
        branch_name = "feature/{}".format(feature_name)
        self._start_feature_branch(branch_name, base_branch)
        yield self
        self._finish_feature_branch(branch_name, base_branch, push)
