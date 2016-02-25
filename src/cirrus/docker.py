#!/usr/bin/env python
"""
docker command


"""
import sys
import subprocess

from argparse import ArgumentParser
from cirrus.logger import get_logger
from cirrus.configuration import load_configuration
import dockerstache.dockerstache as ds

LOGGER = get_logger()


class OptionHelper(dict):
    """helper class to resolve cli and cirrus conf opts"""
    def __init__(self, cli_opts, config):
        super(OptionHelper, self).__init__()
        self['username'] = config.get_param('docker', 'docker_login_username', None)
        self['email'] = config.get_param('docker', 'docker_login_email', None)
        self['password'] = config.get_param('docker', 'docker_login_password', None)
        self['login'] = config.get_param(
            'docker', 'docker_login_username', None
        ) is not None
        self['tag'] = None

        if cli_opts.login:
            self['login'] = True
        if hasattr(cli_opts, 'tag'):
            if cli_opts.tag:
                self['tag'] = cli_opts.tag


class BuildOptionHelper(OptionHelper):
    """helper class to resolve cli and cirrus conf opts for build"""
    def __init__(self, cli_opts, config):
        super(BuildOptionHelper, self).__init__(cli_opts, config)
        self['docker_repo'] = config.get_param('docker', 'repo', None)
        self['directory'] = config.get_param('docker', 'directory', None)
        self['template'] = config.get_param('docker', 'dockerstache_template', None)
        self['context'] = config.get_param('docker', 'dockerstache_context', None)
        self['defaults'] = config.get_param('docker', 'dockerstache_defaults', None)
        if cli_opts.docker_repo:
            self['docker_repo'] = cli_opts.docker_repo
        if cli_opts.directory:
            self['directory'] = cli_opts.directory
        if cli_opts.dockerstache_template:
            self['template'] = cli_opts.dockerstache_template


def build_parser():
    """
    _build_parser_

    Set up command line parser for the deploy command

    """
    parser = ArgumentParser(
        description='git cirrus docker command'
    )
    parser.add_argument('command', nargs='?')

    subparsers = parser.add_subparsers(dest='command')
    build_command = subparsers.add_parser('build')
    build_command.add_argument(
        '--docker-repo', '-r',
        dest='docker_repo',
        help='docker repository name',
        default=None,
    )
    build_command.add_argument(
        '--login',
        action='store_true',
        dest='login',
        help='Perform docker login before command using settings in cirrus.conf',
        default=False
    )
    build_command.add_argument(
        '--directory', '-d',
        dest='directory',
        help='path to directory containing dockerfile to run docker build in',
        default=None,
    )
    build_command.add_argument(
        '--dockerstache-template',
        dest='dockerstache_template',
        default=None,
        help='directory containing dockerstache template to render'
    )
    build_command.add_argument(
        '--dockerstache-context',
        dest='dockerstache_context',
        default=None,
        help='path to dockerstache context file'
    )
    build_command.add_argument(
        '--dockerstache-defaults',
        dest='dockerstache_defaults',
        default=None,
        help='path to dockerstache defaults file'
    )

    push_command = subparsers.add_parser('push')
    push_command.add_argument(
        '--login',
        action='store_true',
        dest='login',
        help='Perform docker login before command using settings in cirrus.conf',
        default=False
    )

    opts = parser.parse_args()
    return opts


def _docker_build(path, tag):
    """
    execute docker build -t <tag> <path> in a subprocess
    """
    command = ['docker', 'build', '-t', tag, path]
    LOGGER.info("Executing docker build command: {}".format(' '.join(command)))
    stdout = subprocess.check_output(command)
    LOGGER.info(stdout)


def _docker_login(helper):
    """
    perform a docker login call using email/user/pass from cirrus.conf
    if present.
    Returns true if login performed, false otherwise
    """
    if helper['username']:
        LOGGER.info("Running docker login as {}".format(helper['username']))
        command = [
            'docker', 'login', '-u', helper['username'], '-e',
            helper['email'], '-p', helper['password']
        ]
        stdout = subprocess.check_output(command)
        LOGGER.info(stdout)
        return True

    LOGGER.info('No docker login credentials provided in cirrus.conf')
    return False


def _docker_push(tag):
    """
    execute docker push command as a subprocess
    """
    command = ['docker', 'push', tag]
    LOGGER.info("Executing docker push command: {}".format(' '.join(command)))
    stdout = subprocess.check_output(command)
    LOGGER.info(stdout)


def tag_name(config):
    """
    build the docker tag string
    """
    pname = config.package_name()
    pversion = config.package_version()
    docker_repo = config.get_param('docker', 'repo', None)
    if docker_repo is None:
        docker_repo = config.organisation_name()
    return "{}/{}:{}".format(docker_repo, pname, pversion)


def docker_build(opts, config):
    """
    issue a docker build command in the directory
    specified.
    Optionally, if a dockerstache template is given, run
    dockerstache using that template and the build directory
    as output
    """
    tag = tag_name(config)
    helper = BuildOptionHelper(opts, config)
    templ = helper['template']
    path = helper['directory']

    if helper['login']:
        check = _docker_login(helper)
        if not check:
            msg = "Unable to perform docker login due to missing cirrus conf entries"
            LOGGER.error(msg)
            sys.exit(1)
    if templ is not None:
        ds.run(
            input=templ,
            output=path,
            context=helper['context'],
            defaults=helper['defaults']
        )

    _docker_build(path, tag)


def docker_push(opts, config):
    """
    run a docker push command to upload the
    tagged image to a registry
    """
    helper = OptionHelper(opts, config)
    if helper['login']:
        check = _docker_login(helper)
        if not check:
            msg = "Unable to perform docker login due to missing cirrus conf entries"
            LOGGER.error(msg)
            sys.exit(1)
    tag = helper['tag']
    if tag is None:
        tag = tag_name(config)
    _docker_push(tag)


def main():
    """
    _main_

    provide support for some basic docker operations so that
    building images can be standardised as part of a workflow
    """
    opts = build_parser()
    config = load_configuration()
    if not config.has_section('docker'):
        msg = (
            "Unable to find docker section in cirrus.conf"
            #TODO: Link to docs here
            )
        LOGGER.error(msg)
        sys.exit(1)
    if opts.command == 'build':
        docker_build(opts, config)
    if opts.command == 'push':
        docker_push(opts, config)


if __name__ == '__main__':
    main()
