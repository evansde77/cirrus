#!/usr/bin/env python
"""
package

Implementation for the package command that handles helping set up and
manipulate packages for use with cirrus.

Commands:

package init - Initialise a new repo with a basic cirrus.conf file
  add the appropriate setup, manifest and requirements files

package sublime-project - Assistant to set up a sublime project for a cirrus
  managed package, including build rules for the local venv

"""
import contextlib
import inspect
import os
import sys

import pystache
import ConfigParser
import pluggage.registry

import cirrus.templates

from argparse import ArgumentParser

from cirrus.logger import get_logger
from cirrus.utils import update_version
from cirrus.git_tools import (
    branch,
    push,
    get_tags,
    tag_release,
    commit_files_optional_push,
    get_active_branch
)


DEFAULT_HISTORY_SENTINEL = "\nCIRRUS_HISTORY_SENTINEL\n"
LOGGER = get_logger()


def get_plugin(plugin_name):
    """
    _get_plugin_

    Get the editor plugin
    """
    factory = pluggage.registry.get_factory(
        'editors',
        load_modules=['cirrus.plugins.editors']
    )
    return factory(plugin_name)


def list_plugins():
    factory = pluggage.registry.get_factory(
        'editors',
        load_modules=['cirrus.plugins.editors']
    )
    return [
        k for k in factory.registry.keys()
        if k != "EditorPlugin"
    ]


def build_parser(argslist):
    """
    build CLI parser and process args
    """
    parser = ArgumentParser(
        description=(
            'git cirrus package command:'
            ' initialises cirrus for an existing git repo'
        )
    )
    parser.add_argument('command', nargs='?')

    subparsers = parser.add_subparsers(dest='command')
    init_command = subparsers.add_parser('init')
    init_command.add_argument(
        '--repo', '-r',
        dest='repo',
        default=os.getcwd()
    )
    init_command.add_argument(
        '--source-dir', '-s',
        help="source code directory within package, assumes top level dir if not set",
        dest='source',
        default=None
    )
    init_command.add_argument(
        '--package', '-p',
        help="name of package being bootstrapped",
        dest='package',
        required=True
    )
    init_command.add_argument(
        '--version', '-v',
        help="initial package version",
        default='0.0.0',
        dest='version'
    )
    init_command.add_argument(
        '--organization', '-o',
        dest='org',
        default='ORGANIZATION HERE',
    )
    init_command.add_argument(
        '--description', '-d',
        dest='desc',
        default='PACKAGE DESCRIPTION HERE'
    )

    init_command.add_argument(
        '--templates',
        help='template rules to include in MANIFEST',
        nargs='+',
        default=list()
    )
    init_command.add_argument(
        '--version-file',
        help='Version file, defaults to package __init__.py',
        default=None
    )
    init_command.add_argument(
        '--history-file',
        help='changelog history filename',
        default='HISTORY.md'
    )
    init_command.add_argument(
        '--requirements',
        help='requirements file for pip',
        default='requirements.txt'
    )
    init_command.add_argument(
        '--master-branch',
        help='GitFlow master branch',
        default='master',
        dest='master'
    )
    init_command.add_argument(
        '--develop-branch',
        help='GitFlow develop branch',
        default='develop',
        dest='develop'
    )
    init_command.add_argument(
        '--no-remote',
        help='disable pushing changes to remote, commit locally only',
        default=False,
        action='store_true'
    )
    init_command.add_argument(
        '--create-version-file',
        help="create the file containing __version__ if it doesn\'t exist",
        default=False,
        action='store_true'
    )

    proj_command = subparsers.add_parser('project')
    proj_command.add_argument(
        '--repo', '-r',
        dest='repo',
        default=os.getcwd()
    )
    proj_command.add_argument(
        '--type', '-t',
        help='type of project to create',
        choices=list_plugins()
    )
    proj_command.add_argument(
        '--pythonpath', '-p',
        nargs='+',
        help='subdirs to include on pythonpath',
        default=list()
    )

    opts = parser.parse_args(argslist)
    return opts


@contextlib.contextmanager
def working_dir(new_dir):
    """
    helper to switch to repo dir and back
    """
    cwd = os.getcwd()
    try:
        os.chdir(new_dir)
        yield new_dir
    finally:
        os.chdir(cwd)


def setup_branches(opts):
    """
    set up git branches, starting from master
    """
    do_push = not opts.no_remote
    LOGGER.info(
        "setting up branches master={} develop={}".format(
            opts.master, opts.develop
        )
    )
    with working_dir(opts.repo):
        branch(opts.repo, opts.master, opts.master)
        branch(opts.repo, opts.develop, opts.master)
        if do_push:
            LOGGER.info("Pushing {}...".format(opts.develop))
            push(opts.repo)

    LOGGER.info("Working on {}".format(get_active_branch(opts.repo)))


def commit_and_tag(opts, *files):
    """
    add files, commit changes and verify that initial tag
    exists

    """
    do_push = not opts.no_remote
    commit_files_optional_push(
        opts.repo,
        "git cirrus package init",
        do_push,
        *files
    )

    tags = get_tags(opts.repo)
    if opts.version not in tags:
        msg = (
            "tag {} not found, tagging {}..."
        ).format(opts.version, opts.master)
        LOGGER.info(msg)
        tag_release(
            opts.repo,
            opts.version,
            master=opts.master,
            push=do_push
        )
    branch(opts.repo, opts.develop, opts.develop)


def backup_file(filename):
    """
    if filename exists, make a .BAK copy of it to avoid clobbering
    any existing files.

    """
    if not os.path.exists(filename):
        return
    newfile = "{}.BAK".format(filename)
    LOGGER.info("Backing up {} to {}".format(filename, newfile))
    with open(filename, 'r') as handle_in:
        content = handle_in.read()

    with open(newfile, 'w') as handle_out:
        handle_out.write(content)


def write_manifest(opts):
    """
    write the manifest file used for distribution

    """
    manifest = os.path.join(opts.repo, 'MANIFEST.in')
    backup_file(manifest)
    LOGGER.info("setting up manifest: {}".format(manifest))
    lines = [
        "include requirements.txt",
        "include cirrus.conf"
    ]
    lines.extend(opts.templates)

    with open(manifest, 'w') as handle:
        for line in lines:
            handle.write("{}\n".format(line))
    return manifest


def write_setup_py(opts):
    """
    write setup.py for the new package, using
    the cirrus template.
    Placeholder for rendering it with other
    values.

    """
    setup = os.path.join(opts.repo, 'setup.py')
    backup_file(setup)
    LOGGER.info("setting up setup.py: {}".format(setup))
    template = os.path.join(
        os.path.dirname(inspect.getsourcefile(cirrus.templates)),
        'setup.py.mustache'
    )
    with open(template, 'r') as handle:
        templ = handle.read()

    rendered = pystache.render(templ, {})
    with open(setup, 'w') as handle:
        handle.write(rendered)

    return setup


def write_history(opts):
    """
    set up the history file containing the sentinel for
    release notes

    """
    history = os.path.join(opts.repo, opts.history_file)
    LOGGER.info("setting up history file: {}".format(history))
    if not os.path.exists(history):
        with open(history, 'w') as handle:
            handle.write(DEFAULT_HISTORY_SENTINEL)
    else:
        with open(history, 'a') as handle:
            handle.write(DEFAULT_HISTORY_SENTINEL)
    return history


def write_cirrus_conf(opts, version_file):
    """
    build the basic cirrus config file and write it out

    """
    cirrus_conf = os.path.join(opts.repo, 'cirrus.conf')
    LOGGER.info("setting up cirrus.conf: {}".format(cirrus_conf))
    backup_file(cirrus_conf)
    config = ConfigParser.ConfigParser()
    config.add_section('package')
    config.set('package', 'name', opts.package)
    config.set('package', 'version', opts.version)
    config.set('package', 'description', opts.desc)
    config.set('package', 'organization', opts.org)
    config.set('package', 'version_file', version_file)
    config.set('package', 'history_file', opts.history_file)
    config.set('package', 'author',  os.environ['USER'])
    config.set('package', 'author_email', 'EMAIL_HERE')
    config.set('package', 'url', 'PACKAGE_URL_HERE')
    if opts.source:
        config.set('package', 'find_packages', opts.source)

    config.add_section('gitflow')
    config.set('gitflow', 'develop_branch', opts.develop)
    config.set('gitflow', 'release_branch_prefix', 'release/')
    config.set('gitflow', 'feature_branch_prefix', 'feature/')

    config.add_section('test-default')
    config.set('test-default', 'TESTDIRHERE')

    config.add_section('quality')
    config.set('quality', 'threshold', 10)

    with open(cirrus_conf, 'w') as handle:
        config.write(handle)
    return cirrus_conf


def update_package_version(opts):
    """
    set and/or update package __version__
    attr
    """
    version_file = opts.version_file
    if version_file is None:
        elems = [opts.repo]
        if opts.source:
            elems.append(opts.source)
        elems.append(opts.package)
        elems.append('__init__.py')
        version_file = os.path.join(*elems)
    if not os.path.exists(version_file):
        msg = (
            "unable to find version file: {}"
        ).format(version_file)
        LOGGER.info(msg)
        if opts.create_version_file:
            with open(version_file, 'w') as handle:
                handle.write("# created by cirrus package init\n")
                handle.write("__version__ = \"{}\"".format(opts.version))
            LOGGER.info("creating version file: {}".format(version_file))
        else:
            msg = (
                "Unable to update version file, please verify the path {}"
                " is correct. Either provide the --version-file"
                " option pointing"
                " to an existing file or set the --create-version-file"
                " flag to create a new file"
            ).format(version_file)
            LOGGER.error(msg)
            sys.exit(1)

    update_version(version_file, opts.version)
    return version_file


def create_files(opts):
    """
    create files and return a list of the
    files that need to be committed
    """
    files = []
    files.append(write_manifest(opts))
    files.append(write_setup_py(opts))
    files.append(write_history(opts))

    vers_file = update_package_version(opts)
    files.append(vers_file)
    files.append(write_cirrus_conf(opts, vers_file))
    return files


def init_package(opts):
    """
    initialise a repo with a basic cirrus setup
    """
    setup_branches(opts)
    # write files
    files = create_files(opts)
    with working_dir(opts.repo):
        commit_and_tag(opts, *files)

    msg = (
        "\nA basic cirrus.conf file has been added to your package\n"
        "please review it and add any additional fields and commit it\n"
        "The files have been added to the {} branch"
    ).format(opts.develop)
    LOGGER.info(msg)


def build_project(opts):
    """
    create an editor/ide project for the repo
    """
    pname = opts.type
    plugin = get_plugin(pname)
    plugin.run(opts)


def main():
    """
    main cli response handler
    """
    opts = build_parser(sys.argv)

    if opts.command == 'init':
        init_package(opts)

    if opts.command == 'project':
        build_project(opts)


if __name__ == '__main__':
    main()
