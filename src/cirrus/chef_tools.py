#!/usr/bin/env python
"""
_chef_tools_

Helpers/utils for modifying chef objects on the server and in a local repo

"""
import os
import git
import json
import chef

from contextlib import contextmanager


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
    with chef.ChefAPI(server_url, cert,username):
        env = chef.Environment(environment)
        overrides = env.override_attributes
        for attr, new_value in attributes.iteritems():
            set_dotted(overrides, attr, new_value)

def edit_chef_role(server_url, cert, username, rolename, attributes):
    """
    _edit_chef_role_

    For a given chef server, edit the override attributes in the named role
    making changes for each dotted key:value pair in attributes.

    """
    with chef.ChefAPI(server_url, cert,username):
        role = chef.Role(rolename)
        overrides = role.override_attributes
        for attr, new_value in attributes.iteritems():
            set_dotted(overrides, attr, new_value)


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
        self.envs = options.get('environments_dir', 'environments')
        self.roles = options.get('roles_dir', 'roles')

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
        new_commit = self.repo.index.commit(commit_msg)
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
            data = json.dump(data, handle, indent=2)
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
    def edit_environment(self, environment, branch='master', message=None):
        """
        context manager that allows you to edit,
        save and commit an environment

        """
        self.checkout_and_pull(branch)
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
        roles_dir = os.path.join(self.repo_dir, self.roles)
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
        return self._read_json_file(self.roles, role)

    def save_role(self, role, role_data):
        """
        _save_role_

        Write formatted json to file
        """
        self._write_json_file(self.roles, role, role_data)
        return '{0}/{1}.json'.format(self.roles, role)

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
