#!/usr/bin/env python2.7
"""
_bootstrap_

cirrus python bootstrap script invoked by the bash installer script

"""
import os
import sys
import json
import getpass
import gitconfig
import requests
from xml.dom.minidom import parseString

GITHUB_AUTH_URL = "https://api.github.com/authorizations"

def ask_question(question, default=None, valid=None):
    """
    _ask_question_

    Ask a question on stdin

    """
    to_ask = "{0}".format(question)
    if default is not None:
        to_ask += " [{0}]: ".format(default)
    else:
        to_ask += ": "
    result = raw_input(to_ask)
    if result.strip() == '':
        if default is not None:
            result = default
        else:
            msg = "No response provided for question"
            print msg
            raise RuntimeError(msg)
    if valid is not None:
        if result not in valid:
            msg = "Invalid input: {0} must be one of {1}".format(
                result, valid
            )
            print msg
            raise RuntimeError(msg)
    return result

def create_github_token(git_config):
    """
    _create_github_token_

    Prompts for github user and pass and generates an access
    token which is added to .gitconfig

    We first look for tokens that are present with cirrus in
    the notes field and use that if it exists.

    If not we proceed to generate a token and save it to .gitconfig

    Once the token is in place we can use it to make github API
    requests for things like pull requests

    """
    user = ask_question('what is your github username?', default=os.environ['USER'])
    passwd = getpass.getpass('what is your github password?')
    resp = requests.get(GITHUB_AUTH_URL, auth=(user, passwd))
    resp.raise_for_status()
    apps = resp.json()
    matched_app = None
    for app in apps:
        if app['app']['name'] == 'cirrus script (API)':
            matched_app = app
            print "Token found for cirrus script... reusing it..."
            break

    if matched_app is None:
        # need to create a new token
        print "Creating a new Token for github access..."
        resp = requests.post(
            GITHUB_AUTH_URL,
            auth=(user, passwd),
            data=json.dumps({"scopes":["gist","repo"], "note": "cirrus script"})
            )
        resp.raise_for_status()
        matched_app = resp.json()

    token = matched_app['token']
    url = matched_app['url']
    git_config.set('cirrus', 'github-user', user)
    git_config.set('cirrus', 'github-token', token)
    git_config.set('cirrus', 'github-url', url)
    del passwd
    return


def insert_pypi_credentials(git_config, auto_yes=False):
    """
    prompt the user to provide pypi credentials if not present

    """
    user = git_config.get('cirrus', 'pypi-user')
    token = git_config.get('cirrus', 'pypi-token')
    key = git_config.get('cirrus', 'pypi-ssh-key')
    if user is None:
        if auto_yes:
            print "Please add pypi-user to the .gitconfig prior to use"
        else:
            user = ask_question(
                'what is your pypi username?',
                default=os.environ['USER']
            )
            git_config.set('cirrus', 'pypi-user', user)
    if token is None:
        if auto_yes:
            print "Please add pypi-token to the .gitconfig prior to use"
        else:
            token = ask_question(
                'what is your pypi token/password?',
                default='notprovided'
            )
            git_config.set('cirrus', 'pypi-token', token)
    if key is None:
        if auto_yes:
            print "Please add pypi-ssh-key to the .gitconfig prior to use"
        else:
            key = ask_question(
                'what is your pypi upload ssh key?',
                default=os.path.join(os.environ['HOME'], '.ssh', 'id_rsa')
            )
            git_config.set('cirrus', 'pypi-ssh-key', key)
    return


def read_gitconfig(auto_yes=False):
    """
    _read_gitconfig_

    Looks for ~/.gitconfig and reads it to determine wether
    there is already a token for github access

    """
    gitconfig_file = os.path.join(os.environ['HOME'], '.gitconfig')
    config = gitconfig.config(gitconfig_file)
    github_token = config.get('cirrus', 'github-token')
    if github_token is None:
        if auto_yes:
            print (
                "There is no github-token in the .gitconfig file,"
                " please update this file prior to use"
            )
        else:
            print "We need to generate a github access token"
            print "Please enter you github username and password when prompted"
            print "(Dont worry, they arent stored just used to create the token)"
            create_github_token(config)
    else:
        print "Looks like you already have a github token in .gitconfig..."

    insert_pypi_credentials(config, auto_yes)

    return config

def update_shell_profile():
    """
    _update_shell_profile_

    append a line that sets CIRRUS_HOME to ~/.bash_profile
    or ~/.bashrc whichever one is chosen.

    In case of non-bash shell, user is on their own due to
    being weird

    """
    cirrus_home = os.environ['CIRRUS_HOME']
    if os.environ.get('SHELL') == '/bin/bash':
        bash_prof = '{0}/.bash_profile'.format(os.environ['HOME'])
        bash_rc = '{0}/.bashrc'.format(os.environ['HOME'])
        if os.path.exists(bash_prof):
            default = bash_prof
        else:
            default = bash_rc
        bash = ask_question(
            'what is your bash_profile file?',
            default=default
        )

        newline = 'export CIRRUS_HOME={0}'.format(cirrus_home)
        print 'adding CIRRUS_HOME to {0}...'.format(bash)
        print newline

        # dupe prevention
        dupe_found = None
        for line in  open(bash, 'r'):
            if line.startswith('export CIRRUS_HOME'):
                dupe_found = line
        if dupe_found is None:
            with open(bash, 'a') as handle:
                handle.write("\n")
                handle.write(newline)
                handle.write("\n")
        else:
            if dupe_found != newline:
                msg = (
                    "Looks like your bash profile {0} already contains a CIRRUS_HOME "
                    "Please verify it is set to {1} after this script completes"
                ).format(bash, cirrus_home)
                print msg

    else:
        print "Please add the environment variable setting:"
        print "CIRRUS_HOME={0}".format(os.environ['CIRRUS_HOME'])
        print "To the rc/startup file of whatever shell you are using"


def main():
    """
    main installer call

    - Sets up github access token
    - Sets up FB access token
    - Sets up full virtualenv installation
    - Adds aliases to git pointing at the commands defined in src
    - Adds export CIRRUS_HOME to bash_profile or bashrc, or complains
      about people who dont use bash

    """
    auto_yes = False
    if any('--yes' in sys.argv, '-y' in sys.argv):
        auto_yes = True
    config = read_gitconfig(auto_yes)
    #update_shell_profile()
    # set the git alias in gitconfig
    config.set(
        'alias',
        'cirrus',
        '! {0}/bin/cirrus'.format(os.environ['VIRTUALENV_HOME'])
    )


if __name__ == '__main__':
    main()
