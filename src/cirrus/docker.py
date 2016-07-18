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

DOCKER_CONNECTION_HELP = """
We could not connect to a docker daemon.

If you are using docker-machine, run 'docker-machine env <name>' and follow the
instructions to configure your shell.

If you are running docker natively, check that the docker service is running
and you have sufficient privileges to connect.
"""


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

        if cli_opts.login:
            self['login'] = True


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

    Set up command line parser for the docker-image command

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
        help='perform docker login before command using settings in cirrus.conf',
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
        help='perform docker login before command using settings in cirrus.conf',
        default=False
    )
    push_command.add_argument(
        '--latest',
        action='store_true',
        dest='latest',
        help='include the image tagged "latest" in the docker push command',
        default=False
    )

    subparsers.add_parser('test', help='test docker connection')
    opts = parser.parse_args()
    return opts


def _docker_build(path, tag, base_tag):
    """
    execute docker build -t <tag> <path> in a subprocess
    """
    command = ['docker', 'build', '-t', tag, path]
    LOGGER.info("Executing docker build command: {}".format(' '.join(command)))
    try:
        stdout = subprocess.check_output(command)
    except subprocess.CalledProcessError as ex:
        LOGGER.error(ex.output)
        raise
    LOGGER.info(stdout)
    image = find_image_id(base_tag)
    LOGGER.info("Image ID: {}".format(image))
    return image


def find_image_id(base_tag):
    """
    grab the last created image id for the repo
    """
    command = (
        "echo $(docker images | grep '{tag}' | "
        "head -n 1 | awk '{{print $3}}')"
    ).format(tag=base_tag)
    process = subprocess.Popen([command], shell=True, stdout=subprocess.PIPE)
    outp, err = process.communicate()
    LOGGER.info("Latest Container: {}".format(outp))
    return outp.strip()


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


def _docker_tag(image, tag, latest):
    """
    tag the created image ID with the current tag and as latest
    Note that this uses tag -f
    """
    command = ['docker', 'tag', '-f', image, tag]
    LOGGER.info("Executing {}".format(' '.join(command)))
    try:
        stdout = subprocess.check_output(command)
    except subprocess.CalledProcessError as ex:
        LOGGER.error(ex.output)
        raise
    LOGGER.info(stdout)
    command = ['docker', 'tag', '-f', image, latest]
    LOGGER.info("Executing {}".format(' '.join(command)))
    try:
        stdout = subprocess.check_output(command)
    except subprocess.CalledProcessError as ex:
        LOGGER.error(ex.output)
        raise
    LOGGER.info(stdout)


def _docker_push(tag):
    """
    execute docker push command as a subprocess
    """
    command = ['docker', 'push', tag]
    LOGGER.info("Executing docker push command: {}".format(' '.join(command)))
    stdout = subprocess.check_output(command)
    LOGGER.info(stdout)


def tag_base(config):
    pname = config.package_name()
    docker_repo = config.get_param('docker', 'repo', None)
    if docker_repo is None:
        docker_repo = config.organisation_name()
    return "{}/{}".format(docker_repo, pname)


def tag_name(config):
    """
    build the docker tag string
    """
    pversion = config.package_version()
    return "{}:{}".format(tag_base(config), pversion)


def latest_tag_name(config):
    return "{}:latest".format(tag_base(config))


def docker_build(opts, config):
    """
    issue a docker build command in the directory
    specified.
    Optionally, if a dockerstache template is given, run
    dockerstache using that template and the build directory
    as output
    """
    tag = tag_name(config)
    latest = latest_tag_name(config)
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
            defaults=helper['defaults'],
            extend_context=config.configuration_map()
        )

    image = _docker_build(path, tag, tag_base(config))
    _docker_tag(image, tag, latest)


def docker_push(opts, config):
    """
    run a docker push command to upload the
    tagged image to a registry
    """
    helper = OptionHelper(opts, config)
    if helper['login']:
        if not _docker_login(helper):
            msg = "Unable to perform docker login due to missing cirrus conf entries"
            LOGGER.error(msg)
            sys.exit(1)

    tag = tag_name(config)
    _docker_push(tag)

    if opts.latest:
        _docker_push(latest_tag_name(config))


def is_docker_connected():
    """
    Tests whether the docker daemon is connected using  the 'docker info'
    native command
    """
    try:
        subprocess.check_output(['docker', 'info'], stderr=subprocess.STDOUT)
        LOGGER.info("Docker daemon connection successful")
    except subprocess.CalledProcessError as ex:
        LOGGER.error(ex)
        LOGGER.error(ex.output.strip())
        return False
    return True


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

    if not is_docker_connected():
        LOGGER.error(DOCKER_CONNECTION_HELP)
        sys.exit(1)

    if opts.command == 'build':
        docker_build(opts, config)
    if opts.command == 'push':
        docker_push(opts, config)
    if opts.command == 'test':
        # Already called above
        pass


if __name__ == '__main__':
    main()
