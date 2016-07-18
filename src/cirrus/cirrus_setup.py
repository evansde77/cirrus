#!/usr/bin/env python
"""
selfsetup command to prompt for/configure cirrus post install
"""
import os
import sys
import json
import getpass
import requests

from argparse import ArgumentParser

from cirrus.configuration import load_setup_configuration, get_creds_plugin
from cirrus.logger import get_logger

LOGGER = get_logger()
GITHUB_AUTH_URL = "https://api.github.com/authorizations"


def ask_question(question, default=None, valid=None):
    """
    _ask_question_

    Ask a question on stdin

    :param question: text to pose a question to the user on the command line
    :param default: Default arg that can be accepted by hitting enter
    :param valid: iterable/sequence of acceptable answers to test against

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
            LOGGER.error(msg)
            raise RuntimeError(msg)
    if valid is not None:
        if result not in valid:
            msg = "Invalid input: {0} must be one of {1}".format(
                result, valid
            )
            LOGGER.error(msg)
            raise RuntimeError(msg)
    return result


def create_github_token():
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
    user = ask_question(
        'what is your github username?',
        default=os.environ['USER']
    )
    passwd = getpass.getpass('what is your github password?')
    resp = requests.get(GITHUB_AUTH_URL, auth=(user, passwd))
    resp.raise_for_status()
    apps = resp.json()
    matched_app = None
    for app in apps:
        if app['app']['name'] == oauth_note:
            matched_app = app
            LOGGER.info("Token found for cirrus script... reusing it...")
            break

    if matched_app is None:
        # need to create a new token
        LOGGER.info("Creating a new Token for github access...")
        resp = requests.post(
            GITHUB_AUTH_URL,
            auth=(user, passwd),
            data=json.dumps(
                {"scopes": ["gist", "repo"], "note": oauth_note}
                )
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


def request_ssh_credentials():
    """
    prompt the user to provide ssh credentials if not present

    """
    result = {'username': None, 'keyfile': None}

    user = ask_question(
        'what is your ssh username?',
        default=os.environ['USER']
    )
    keyfile = ask_question(
        'what is your ssh key location?',
        default=os.path.join(os.environ['HOME'], '.ssh', 'id_rsa')
    )
    result['username'] = user
    result['keyfile'] = keyfile
    return result


def request_docker_credentials(auto_yes=False):
    """
    prompt the user for docker credentials

    """
    result = {'username': None, 'token': None, 'email': None}
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
    email = ask_question(
        'what is your docker repo email?',
        default=None
    )
    token = getpass.getpass('what is your docker registry token/password?')
    result['email'] = email
    result['username'] = user
    result['token'] = token
    return result


def request_buildserver_credentials():
    """
    prompt the user to see if a buildserver is being used, and if so
    prompt the user to provide buildserver credentials if not present

    """
    result = {'username': None, 'token': None}

    buildserver = ask_question(
        (
            'Are you triggering releases with a '
            'remote buildserver, eg Jenkins [y/N]?'
        ),
        default='n'
        )
    if 'n' in buildserver.lower():
        return result

    user = ask_question(
        'what is your buildserver username (skip if no buildserver)?',
        default=os.environ['USER']
    )
    token = getpass.getpass('what is your buildserver token/password?')
    result['username'] = user
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
        default=None,
    )
    parser.add_argument(
        '--robot', '-r',
        dest='robot_mode',
        action='store_true',
        help='Non interactive robot mode installer',
        default=False
    )
    parser.add_argument(
        '--pypi-username',
        default=None,
        help='pypi username'
    )
    parser.add_argument(
        '--pypi-token',
        default=None,
        help='pypi access token'
    )
    parser.add_argument(
        '--github-token',
        default=None,
        help='github access token'
    )
    parser.add_argument(
        '--github-username',
        default=None,
        help='github username'
    )
    parser.add_argument(
        '--ssh-username',
        default=None,
        help='ssh username'
    )
    parser.add_argument(
        '--ssh-keyfile',
        default=None,
        help='ssh keyfile path'
    )

    parser.add_argument(
        '--docker-email', 
        default=None, 
        help='dockerhub email address'
    )
    parser.add_argument(
        '--docker-username',
        default=None, 
        help='dockerhub username'
    )
    parser.add_argument(
        '--docker-token',
        default=None, 
        help='dockerhub access token'
    )
    parser.add_argument(
        '--buildserver-username',
        default=None, 
        help='buildserver username'
    )
    parser.add_argument(
        '--buildserver-token',
        default=None, 
        help='buildserver access token'
    )

    opts = parser.parse_args(argslist)
    return opts


def interactive_setup(opts, config):
    """
    interactive Q&A style config

    """
    #TODO: Allow cli options if provided instead of prompting
    gh_creds = config.credentials.github_credentials()
    if gh_creds['github_user'] is None:
        values = create_github_token()
        config.credentials.set_github_credentials(
            values['github-user'], values['github-token']
        )

    pypi_creds = config.credentials.pypi_credentials()
    if pypi_creds['username'] is None:
        values = request_pypi_credentials()
        config.credentials.set_pypi_credentials(
            values['username'], values['token']
        )
    ssh_creds = config.credentials.ssh_credentials()
    if ssh_creds['ssh_username'] is None:
        values = request_ssh_credentials()
        config.credentials.set_ssh_credentials(
            values['username'], values['keyfile']
        )

    build_creds = config.credentials.buildserver_credentials()
    if build_creds['buildserver-user'] is None:
        values = request_buildserver_credentials()
        config.credentials.set_buildserver_credentials(
            values['username'], values['token']
        )

    docker_creds = config.credentials.dockerhub_credentials()
    if docker_creds['username'] is None:
        values = request_docker_credentials()
        config.credentials.set_dockerhub_credentials(
            values['email'], values['username'], values['token']
        )


def robot_setup(opts, config):
    """non interactive setup where creds are passed in as CLI opts"""
    if opts.pypi_username:
        config.credentials.set_pypi_credentials(
            opts.pypi_username, opts.pypi_token
        )
    if opts.github_username:
        config.credentials.set_github_credentials(
            opts.github_username, opts.github_token
        )
    if opts.ssh_username:
        config.credentials.set_ssh_credentials(
            opts.ssh_username, opts.ssh_keyfile
        )
    if opts.docker_username:
        config.credentials.set_dockerhub_credentials(
            opts.docker_email, opts.docker_username, opts.docker_token
        )
    if opts.buildserver_username:
        config.credentials.set_buildserver_credentials(
            opts.buildserver_username, opts.buildserver_token
        )
    return


def main():
    """
    _main_

    Execute selfsetup command
    """
    opts = build_parser(sys.argv[1:])
    config = load_setup_configuration()

    # make sure gitconfig has a cirrus section
    if 'cirrus' not in config.gitconfig.sections:
        config.gitconfig.add_section('cirrus')
    config.gitconfig.set_param(
        'alias',
        'cirrus',
        '! {0}/bin/cirrus'.format(os.environ['VIRTUALENV_HOME'])
    )

    # make sure the creds plugin value is set
    if opts.cred_plugin is not None:
        config._set_creds_plugin(opts.cred_plugin)

    if not opts.robot_mode:
        interactive_setup(opts, config)
    else:
        robot_setup(opts, config)



if __name__ == '__main__':
    main()
