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
from cirrus._2to3 import ConfigParser
import pluggage.registry

import cirrus.templates

from argparse import ArgumentParser

from cirrus.logger import get_logger
from cirrus.utils import working_dir
from cirrus.package_container import init_container
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

TOXFILE = \
"""
[tox]
envlist = {python}
[testenv]
deps=
  -r{requirements}
  -r{test_requirements}
commands=nosetests -w {testdir}/unit
"""


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
        '--tests',
        help='test dir name',
        default='tests'
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
        '--pypi-package-name',
        help='Name for package on upload to pypi, use if different from package option',
        default=None
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
        '--test-requirements',
        help='test requirements file for pip',
        default='test-requirements.txt',
        dest='test_requirements'
    )
    init_command.add_argument(
        '--python',
        help='optionally specify the name of python binary to use in this package, eg python2, python3',
        default=None
    )
    init_command.add_argument(
        '--test-mode',
        help='test execution mode',
        choices=['nosetests', 'tox'],
        default='tox',
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

    init_command.add_argument(
        '--bootstrap',
        help="assumes repo is empty and will create a very minimal set of files to get things started",
        default=False,
        action='store_true'
    )

    cont_command = subparsers.add_parser('container-init')
    cont_command.add_argument(
        '--repo', '-r',
        dest='repo',
        default=os.getcwd()
    )
    cont_command.add_argument(
        '--template-dir',
        help="container template dir in repo",
        default='container-template'
    )
    cont_command.add_argument(
        '--image-dir',
        help="container image build cache dir in repo",
        default='image-dir'
    )
    cont_command.add_argument(
        '--base-image', '-b',
        help="Base image for your docker container",
        dest='container',
        required=True
    )
    cont_command.add_argument(
        '--entrypoint', '-e',
        help='container entrypoint',
        default='/bin/bash'
    )
    cont_command.add_argument(
        '--docker-registry',
        default=None,
        help='docker-registry address'
    )
    cont_command.add_argument(
        '--container-virtualenv',
        default=None,
        dest='virtualenv',
        help="If container image has a virtualenv, install package there, otherwise will install in whatever is system python"
    )
    cont_command.add_argument(
        '--local-install',
        default=False,
        action='store_true',
        help="Add scripts to install from local dist package on container"
    )
    cont_command.add_argument(
        '--pypi-install',
        default=False,
        action='store_true',
        help="Add scripts to install latest version of lib from a pypi server"
    )
    cont_command.add_argument(
        '--no-remote',
        help='disable pushing changes to remote, commit locally only',
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
        "include {}".format(opts.requirements),
        "include {}".format(opts.test_requirements),
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
    pname = opts.package
    if opts.pypi_package_name:
        pname = opts.pypi_package_name
    config = ConfigParser.ConfigParser()
    config.add_section('package')
    config.set('package', 'name', pname)
    config.set('package', 'version', str(opts.version))
    config.set('package', 'description', str(opts.desc))
    config.set('package', 'organization', str(opts.org))
    config.set('package', 'version_file', version_file)
    config.set('package', 'history_file', opts.history_file)
    config.set('package', 'author',  os.environ['USER'])
    config.set('package', 'author_email', 'EMAIL_HERE')
    config.set('package', 'url', 'PACKAGE_URL_HERE')
    if opts.source:
        config.set('package', 'find_packages', str(opts.source))

    config.add_section('gitflow')
    config.set('gitflow', 'develop_branch', str(opts.develop))
    config.set('gitflow', 'release_branch_prefix', 'release/')
    config.set('gitflow', 'feature_branch_prefix', 'feature/')
    config.add_section('build')
    if os.path.exists(opts.test_requirements):
        config.set(
            'build',
            'extra_requirements',
            opts.test_requirements
        )
    if opts.python:
        config.set(
            'build',
            'python',
            opts.python
        )

    config.add_section('test-default')
    config.set('test-default', 'where', 'tests/unit')
    config.set('test-default', 'mode', str(opts.test_mode))

    config.add_section('quality')
    config.set('quality', 'threshold', str(10))

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
        version_file = os.path.join(opts.repo, main_init_file(opts))

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
    if version_file.startswith(opts.repo):
        version_file = version_file.replace(opts.repo, '')
        if version_file.startswith('/'):
            version_file = version_file[1:]
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


def make_package_dir(directory, pkgname):
    # TODO: validate package name
    if pkgname.count('.') > 0:
        package_dirs = pkgname.split('.')
    else:
        package_dirs = [pkgname]

    results = []
    pathname = directory
    while package_dirs:
        d = package_dirs.pop(0)
        pathname = os.path.join(pathname, d)
        init_file = os.path.join(pathname, '__init__.py')
        os.makedirs(pathname)
        with open(init_file, 'w') as handle:
            handle.write("#created by cirrus\n")
        LOGGER.info("wrote: {}".format(init_file))
        results.append(init_file)
    return results


def main_init_file(opts):
    package = opts.package
    if package.count('.') > 0:
        package_dirs = package.split('.')
    else:
        package_dirs = [package]

    elems = []
    if opts.source:
        elems.append(opts.source)
    elems.extend(package_dirs)
    elems.append('__init__.py')
    return os.path.join(*elems)


def bootstrap_repo(opts):
    """
    bootstrap an empty repo with initial
    file and dir structure.

    This adds:

     - src/<package>/__init__.py
     - test/unit/<package>/example_test.py
     - requirements.txt
     - test-requirements.txt
     - tox.ini
    """
    package = opts.package

    if opts.source is None:
        opts.source = 'src'

    files = []
    src_dir = opts.source
    tests_dir = os.path.join(opts.tests)
    unit_dir = os.path.join(tests_dir, 'unit')
    init_files = [
        os.path.join(tests_dir, '__init__.py'),
        os.path.join(unit_dir, '__init__.py'),
    ]
    for d in [src_dir, tests_dir, unit_dir]:
        os.makedirs(d)

    for i in init_files:
        with open(i, 'w') as handle:
            handle.write("#created by cirrus\n")
        files.append(i)

    src_inits = make_package_dir(src_dir, package)
    test_inits = make_package_dir(unit_dir, package)
    files.extend(src_inits)
    files.extend(test_inits)

    test_pkg_dir = os.path.dirname(test_inits[-1])

    main_init = main_init_file(opts)
    with open(main_init, 'w') as handle:
        handle.write("#!/usr/bin/env python\n")
        handle.write("# created by cirrus\n")
        handle.write("__version__=\'{}\'\n".format(opts.version))

    if not os.path.exists(opts.requirements):
        with open(opts.requirements, 'w') as handle:
            handle.write("requests\n")
        files.append(opts.requirements)

    if not os.path.exists(opts.test_requirements):
        with open(opts.test_requirements, 'w') as handle:
            handle.write("tox\n")
            handle.write("nose\n")
            handle.write("coverage\n")
            handle.write("mock\n")
            handle.write("pep8\n")
        files.append(opts.test_requirements)

    if not os.path.exists('tox.ini'):
        if opts.python is not None:
            py_vers = opts.python.replace('python', 'py')
        else:
            py_vers = "py{}.{}".format(
                sys.version_info.major,
                sys.version_info.minor
            )
        with open('tox.ini', 'w') as handle:
            handle.write(
                TOXFILE.format(
                    requirements=opts.requirements,
                    test_requirements=opts.test_requirements,
                    testdir=opts.tests,
                    python=py_vers
                )
            )

        files.append('tox.ini')

    template = os.path.join(
        os.path.dirname(inspect.getsourcefile(cirrus.templates)),
        'sample_test.py.mustache'
    )
    with open(template, 'r') as handle:
        templ = handle.read()

    sample_test = os.path.join(test_pkg_dir, 'sample_test.py')
    rendered = pystache.render(templ, {'package': opts.package})
    with open(sample_test, 'w') as handle:
        handle.write(rendered)
    files.append(sample_test)

    commit_files_optional_push(
        opts.repo,
        "git cirrus package bootstrap",
        False,
        *files
    )


def init_package(opts):
    """
    initialise a repo with a basic cirrus setup
    """
    if opts.bootstrap:
        with working_dir(opts.repo):
            bootstrap_repo(opts)

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

    if opts.command == 'container-init':
        init_container(opts)

    if opts.command == 'project':
        build_project(opts)


if __name__ == '__main__':
    main()
