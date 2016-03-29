#!/usr/bin/env python
"""
selfsetup command to prompt for/configure cirrus post install
"""
import os
import sys
from argparse import ArgumentParser

from cirrus.configuration import load_configuration, get_creds_plugin
from cirrus.logger import get_logger

LOGGER = get_logger()

import os
import sys
import json
import getpass
import requests


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
    oauth_note = "cirrus script"
    user = ask_question('what is your github username?', default=os.environ['USER'])
    passwd = getpass.getpass('what is your github password?')
    resp = requests.get(GITHUB_AUTH_URL, auth=(user, passwd))
    resp.raise_for_status()
    apps = resp.json()
    matched_app = None
    for app in apps:
        if app['app']['name'] == oauth_note:
            matched_app = app
            print "Token found for cirrus script... reusing it..."
            break

    if matched_app is None:
        # need to create a new token
        print "Creating a new Token for github access..."
        resp = requests.post(
            GITHUB_AUTH_URL,
            auth=(user, passwd),
            data=json.dumps({"scopes": ["gist", "repo"], "note": oauth_note})
            )
        resp.raise_for_status()
        matched_app = resp.json()

    token = matched_app['token']
    url = matched_app['url']
    result = {
        'github-user': user,
        'github-token': token,
        'github-url': url,
    }
    del passwd
    return result


def request_pypi_credentials():
    """
    prompt the user to provide pypi credentials if not present

    """
    result = {'username': None, 'token': None}

    user = ask_question(
        'what is your pypi username?',
        default=os.environ['USER']
    )
    token = getpass.getpass('what is your pypi token/password?')
    result['username'] = user
    result['token'] = token
    return result


def request_docker_credentials(auto_yes=False):
    """
    prompt the user for docker credentials

    """
    result = {'user': None, 'token': None, 'email': None}
    use_docker = ask_question(
        'Are you building and uploading docker images? [y/N]?',
        default='n'
        )
    if 'n' in use_docker.lower():
        return result
    user = ask_question(
        'what is your docker repo username?',
        default=os.environ['USER']
    )
    result['user'] = user
    email = ask_question(
        'what is your docker repo email?',
        default=None
    )
    token = getpass.getpass('what is your docker registry token/password?')
    result['email'] = email
    result['user'] = user
    result['token'] = token
    return result


def request_buildserver_credentials():
    """
    prompt the user to see if a buildserver is being used, and if so
    prompt the user to provide buildserver credentials if not present

    """
    result = {'user': None, 'token': None}

    buildserver = ask_question(
        'Are you triggering releases with a remote buildserver, eg Jenkins [y/N]?',
        default='n'
        )
    if 'n' in buildserver.lower():
        return result

    user = ask_question(
        'what is your buildserver username (skip if no buildserver)?',
        default=os.environ['USER']
    )
    token = getpass.getpass('what is your buildserver token/password?')
    result['user'] = user
    result['token'] = token
    return result


def build_parser(argslist):
    """
    _build_parser_

    Set up command line parser for the build command

    : param list argslist: A list of command line arguments
    """
    parser = ArgumentParser(
        description='git cirrus selfsetup'
    )
    parser.add_argument(
        '--credential-plugin', '-c',
        dest='cred_plugin',
        help='Credential plugin manager to use',
        default='default',
    )
    opts = parser.parse_args(argslist)
    return opts


def main():
    """
    _main_

    Execute selfsetup command
    """
    opts = build_parser(sys.argv)
    print opts


if __name__ == '__main__':
    main()

