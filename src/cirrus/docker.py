#!/usr/bin/env python
"""
docker command


"""
import os
import re
import sys
import subprocess
from distutils.version import StrictVersion

from argparse import ArgumentParser, Action
from cirrus.logger import get_logger
from cirrus._2to3 import to_str
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

DOCKER_VERSION_BUILD_HELP = """
Your installed version of "docker build" does not support multiple tag (-t)
arguments. As a result, your image was not auto tagged as "latest".

"docker build -t repo:latest -t repo:1.2.3" is how we apply the "latest" tag to
a new image since "docker tag -f" was deprecated in Docker 1.10.0.

Please consider upgrading your Docker version.
"""

# Version 1.10.0 is needed for "docker build" with multiple -t arguments
DOCKER_REQUIRED_VERSION = '1.10.0'


class DockerVersionError(Exception):
    """
    Custom exception; installed docker version cannot be verified.
    """
    pass


def parse_config_list(s):
    """util to convert X = A,B,C config entry into ['A', 'B', 'C']"""
    return [x.strip() for x in s.split(',') if x.strip()]


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
        self['docker_repo'] = config.get_param('docker', 'repo', None)
        addl_repos = config.get_param('docker', 'additional_repos', None)
        self['additional_repos'] = []
        if addl_repos:
            self['additional_repos'] = parse_config_list(addl_repos)
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
        self['build_arg'] = {}
        self['no_cache'] = config.get_param('docker', 'no_cache', None)
        self['pull'] = config.get_param('docker', 'pull', None)
        if cli_opts.docker_repo:
            self['docker_repo'] = cli_opts.docker_repo
        if cli_opts.directory:
            self['directory'] = cli_opts.directory
        if cli_opts.dockerstache_template:
            self['template'] = cli_opts.dockerstache_template
        if cli_opts.build_arg:
            self['build_arg'].update(cli_opts.build_arg)
        if cli_opts.no_cache:
            self['no_cache'] = True
        if cli_opts.pull:
            self['pull'] = True


class StoreDictKeyPair(Action):
     _DICT = {}
     def __init__(self, option_strings, dest, nargs=None, **kwargs):
         self._nargs = nargs
         super(StoreDictKeyPair, self).__init__(option_strings, dest, nargs=nargs, **kwargs)
     def __call__(self, parser, namespace, values, option_string=None):
         for kv in values:
             k,v = kv.split("=")
             self._DICT[k] = v
         setattr(namespace, self.dest, self._DICT)



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
    build_command.add_argument(
        '--build-arg',
        help='build arg key=value pairs to pass to docker build as build-arg options',
        nargs='+',
        action=StoreDictKeyPair
    )
    build_command.add_argument(
        '--no-cache',
        help='Dont use cached docker layers for build, build from scratch',
        default=False,
        action='store_true'
    )
    build_command.add_argument(
        '--pull',
        help='Dont use cached base docker image for build, re-pull base image from docker-registry',
        default=False,
        action='store_true'
    )
    build_command.add_argument(
        '--local-test',
        help=(
            'install latest dist tarball from ./dist into container '
            'instead of pip installing from remote pypi '
            'Run `git cirrus release build` prior to this to get your latest code '
            'installed for testing'),
        default=False,
        action='store_true'
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


def _docker_build(path, tags, base_tag, build_helper):
    """
    execute docker build <path> in a subprocess

    The build command uses the multiple tag (-t) option provided by
    `docker build` since release 1.10. Otherwise, only the last tag in the list
    is applied.

    :param path: filesystem path containg the build context (Dockerfile)
    :param tags: sequence of tag strings to apply to the image
    :param base_tag: full repository repo/tag string (repository/tag:0)
    """
    command = ['docker', 'build'] + _build_tag_opts(tags)
    if build_helper['no_cache']:
        command.append('--no-cache')
    if build_helper['pull']:
        command.append('--pull')
    if build_helper['build_arg']:
        for k, v in build_helper['build_arg'].items():
            command.extend(["--build-arg", "{}={}".format(k, v)])
    command.append(path)
    LOGGER.info("Executing docker build command: {}".format(' '.join(command)))

    p = subprocess.Popen(
        command,
        stdout=sys.stdout,
        stderr=sys.stderr
        )
    status = p.wait()
    if status:
        msg = "docker build exited non-zero!"
        LOGGER.error(msg)
        raise RuntimeError(msg)

    image = find_image_id(base_tag)
    LOGGER.info("Image ID: {}".format(image))

    if not is_docker_version_installed(DOCKER_REQUIRED_VERSION):
        LOGGER.warning(DOCKER_VERSION_BUILD_HELP)

    return image


def _build_tag_opts(tags):
    """
    create a list of tag options suitable for consumption by
    subprocess.check_output and similar functions.

    >>> _build_tag_opts(['v1.2.3', 'latest'])
    ['-t', 'v1.2.3', '-t', 'latest']

    :param tags: sequence of tag strings
    :returns: list of tag arguments to be fed to docker build.
    """
    tag_opts = []
    for tag in tags:
        tag_opts += ['-t'] + [tag]

    return tag_opts


def is_docker_version_installed(required_version):
    """
    Check that the installed docker version is required_version or greater
    :param required_version: docker version string, such as 1.12.0
    """
    raw_version = get_docker_version()
    installed_version = match_docker_version(raw_version)
    return StrictVersion(installed_version) >= StrictVersion(required_version)


def get_docker_version():
    """
    Find the locally installed docker version, as captured from the output of
    docker -v.

    :returns: the raw string output of docker -v.
    """
    try:
        stdout = subprocess.check_output(('docker', '-v'))
    except subprocess.CalledProcessError as ex:
        LOGGER.error(ex.output)
        raise DockerVersionError(
            "Installed Docker version cannot be determined")
    LOGGER.info(stdout)
    return stdout.strip()


def match_docker_version(raw_version_string):
    """
    Grab the docker version in xx.yy.zz format from a arbitrary string (works
    nicely when fed the output of get_docker_version).

    :param raw_version_string: a string containing a docker version, typically
        in the format returned by docker -v
        "Docker version 1.12.0, build 8eab29e"
    :returns: the docker version string, cleaned up as xx.yy.zz
    """
    match = re.search('[0-9]+\.[0-9]+\.[0-9]+', to_str(raw_version_string))
    if match is None:
        raise DockerVersionError(
            "Installed Docker version cannot be determined. "
            "Could not match '{}'".format(raw_version_string))

    docker_version = match.group().strip()
    return docker_version


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
    return to_str(outp.strip())


def _docker_login(helper):
    """
    perform a docker login call using email/user/pass from cirrus.conf
    if present.
    Returns true if login performed, false otherwise
    """
    if helper['username']:
        LOGGER.info("Running docker login as {}".format(helper['username']))
        command = [
            'docker', 'login',
            '-u', helper['username'],
            '-p', helper['password']
        ]
        if helper.get('docker_repo') is not None:
            command.append(helper['docker_repo'])
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


def tag_base(config):
    pname = config.package_name()
    docker_repo = config.get_param('docker', 'repo', None)
    if docker_repo is None:
        docker_repo = config.organisation_name()
    docker_pkg_pfix = config.get_param('docker', 'package_prefix', None)
    if docker_pkg_pfix is None:
        tag = "{}/{}".format(docker_repo, pname)
    else:
        tag = "{}/{}/{}".format(docker_repo, docker_pkg_pfix, pname)
    return tag

def tag_name(config):
    """
    build the docker tag string
    """
    pversion = config.package_version()
    return "{}:{}".format(tag_base(config), pversion)


def additional_repo_tags(config, repos, latest=False):
    pname = config.package_name()
    pversion = config.package_version()
    result = []
    for repo in repos:
        t_base = "{}/{}".format(repo, pname)
        result.append("{}:{}".format(t_base, pversion))
        if latest:
            result.append("{}:latest".format(t_base))
    return result


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
    if not os.path.exists(path):
        os.makedirs(path)

    if opts.local_test:
        #
        # local test => override build args
        # assumes that the container-init stuff has been used
        local_tar = '/opt/{package}-latest.tar.gz'.format(
            package=config.package_name()
        )
        LOGGER.info("Local test build will install latest source tarball from dist...")
        helper['build_arg']['LOCAL_INSTALL'] = local_tar

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

    tags = [latest, tag]
    if helper['additional_repos']:
        tags.extend(
            additional_repo_tags(
                config,
                helper['additional_repos'],
                latest=True
            )
        )
    _docker_build(path, tags, tag_base(config), helper)


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

    if helper['additional_repos']:
        tags = additional_repo_tags(config, helper['additional_repos'], opts.latest)
        for t in tags:
            _docker_push(t)


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
