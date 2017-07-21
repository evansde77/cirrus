#!/usr/bin/env python
"""
package_container

functions for building the initial docker container
templates for docker-image command

"""
import sys
import os
import json

from cirrus.logger import get_logger
from cirrus.utils import working_dir
from cirrus.configuration import load_configuration
from cirrus.git_tools import (
    commit_files_optional_push,
    checkout_and_pull,
    has_unstaged_changes
)

LOGGER = get_logger()

DOCKER_PRE_SCRIPT = \
"""#!/bin/bash
echo "this is the dockerstache pre render script"
echo "it runs in the following environment before rendering tempates"
printenv | grep DOCKERSTACHE

"""

DOCKER_POST_SCRIPT = \
"""#!/bin/bash
echo "this is the dockerstache post render script"
echo "it runs in the following environment after rendering tempates"
printenv | grep DOCKERSTACHE
{copy_dist}

"""

LOCAL_INSTALL_COMMAND = \
"""
DIST_FILE=`ls -1t ../dist/{package}-*.tar.gz | head -1`
echo "DIST_FILE=${{DIST_FILE}}"
echo "copied to ${{DOCKERSTACHE_OUTPUT_PATH}}"
cp ${{DIST_FILE}} ${{DOCKERSTACHE_OUTPUT_PATH}}
"""

DOCKERFILE_TEMPLATE = \
"""
FROM {container}
MAINTAINER {maintainer}
ADD local_pip_install.sh /opt/local_pip_install.sh
ADD pypi_pip_install.sh /opt/pypi_pip_install.sh
RUN chmod +x /opt/pypi_pip_install.sh /opt/local_pip_install.sh

{local_install}
{pip_install}

ENTRYPOINT ["{entrypoint}"]
"""

LOCAL_INSTALL_SCRIPT = \
"""
#!/bin/bash

{virtualenv}
pip install /opt/{{{{cirrus.configuration.package.name}}}}-{{{{cirrus.configuration.package.version}}}}.tar.gz

"""

PYPI_INSTALL_SCRIPT = \
"""
#!/bin/bash

{virtualenv}
pip install {pip_options} {{{{cirrus.configuration.package.name}}}}=={{{{cirrus.configuration.package.version}}}}

"""

def make_executable(path):
    mode = os.stat(path).st_mode
    mode |= (mode & 0o444) >> 2    # copy R bits to X
    os.chmod(path, mode)


def write_basic_dockerfile(opts, config, path):
    """
    write the basic dockerfile for the example/template

    """
    LOGGER.info("writing Dockerfile {}".format(path))
    pip_install = ""
    if opts.pypi_install:
        pip_install = "RUN /opt/pypi_pip_install.sh"

    local_install = ""
    if opts.local_install:
        local_install = (
            "COPY "
            "{{cirrus.configuration.package.name}}-"
            "{{cirrus.configuration.package.version}}.tar.gz "
            "/opt/"
        )
        pip_install = "RUN /opt/local_pip_install.sh"

    content = DOCKERFILE_TEMPLATE.format(
        container=opts.container,
        entrypoint=opts.entrypoint,
        maintainer=config.author_email(),
        pip_install=pip_install,
        local_install=local_install
        )

    with open(path, 'w') as handle:
        handle.write(content)


def write_json_file(path, data):
    """write json data to a file"""
    LOGGER.info("writing JSON {}".format(path))
    with open(path, 'w') as handle:
        json.dump(data, handle)


def write_script(path, content, **extras):
    """write script content to a file"""
    LOGGER.info("writing script {}".format(path))

    script = content.format(**extras)
    with open(path, 'w') as handle:
        handle.write(script)
    # run chmod +x on new script
    make_executable(path)


def edit_cirrus_conf(opts, config):
    """
    add docker settings to cirrus conf

    """
    LOGGER.info("updating cirrus.conf docker section...")
    config.add_docker_settings(
        opts.template_dir,
        opts.context_file,
        opts.image_dir,
        opts.docker_registry
    )


def init_container(opts):
    """
    Initialise a basic container-template setup
    for this package
    """
    cirrus_conf = os.path.join(opts.repo, 'cirrus.conf')
    if not os.path.exists(cirrus_conf):
        msg = "No cirrus.conf found, need to init repo first?"
        LOGGER.error(msg)
        sys.exit(1)

    config = load_configuration(opts.repo)
    template_dir = os.path.join(opts.repo, opts.template_dir)
    if not os.path.exists(template_dir):
        LOGGER.info("Creating Template in {}".format(template_dir))
        os.makedirs(template_dir)

    docker_file = os.path.join(template_dir, 'Dockerfile.mustache')
    dotfile = os.path.join(template_dir, '.dockerstache')
    pre_script = os.path.join(template_dir, 'pre_script.sh')
    post_script = os.path.join(template_dir, 'post_script.sh')
    context = os.path.join(template_dir, 'context.json')
    local_install = os.path.join(template_dir, 'local_pip_install.sh.mustache')
    pypi_install = os.path.join(template_dir, 'pypi_pip_install.sh.mustache')
    opts.context_file = os.path.join(opts.template_dir, 'context.json')

     # make sure repo is clean
    if has_unstaged_changes(opts.repo):
        msg = (
            "Error: Unstaged changes are present on the branch "
            "Please commit them or clean up before proceeding"
        )
        LOGGER.error(msg)
        raise RuntimeError(msg)

    main_branch = config.gitflow_branch_name()
    LOGGER.info("checking out latest {} branch...".format(main_branch))
    checkout_and_pull(opts.repo,  main_branch, not opts.no_remote)

    venv_option = ""
    if opts.virtualenv:
        venv_option = ". {}/bin/activate".format(opts.virtualenv)

    with working_dir(template_dir):
        write_basic_dockerfile(opts, config, docker_file)
        write_json_file(dotfile, {
            "post_script": "post_script.sh",
            "pre_script": "pre_script.sh",
            "inclusive": True,
            "excludes": ["post_script.sh", "post_script.sh", ".dockerstache"]
        })
        write_json_file(context, {})
        write_script(pre_script, DOCKER_PRE_SCRIPT)
        write_script(
            local_install,
            LOCAL_INSTALL_SCRIPT,
            virtualenv=venv_option
        )
        write_script(
            pypi_install,
            PYPI_INSTALL_SCRIPT,
            virtualenv=venv_option,
            pip_options=config.pip_options() if config.pip_options() else ""
        )
        if opts.local_install:
            write_script(
                post_script,
                DOCKER_POST_SCRIPT,
                copy_dist=LOCAL_INSTALL_COMMAND.format(package=config.package_name())
            )
        else:
            write_script(post_script, DOCKER_POST_SCRIPT, copy_dist="")
        edit_cirrus_conf(opts, config)

        modified = [
            cirrus_conf,
            docker_file,
            dotfile,
            pre_script,
            post_script,
            local_install,
            pypi_install,
            context
        ]
        LOGGER.info("commiting changes...")
        commit_files_optional_push(
            opts.repo,
            "git cirrus package container-init",
            not opts.no_remote,
            *modified
        )
