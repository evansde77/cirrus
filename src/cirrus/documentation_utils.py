#!/usr/bin/env python
"""
_documentation_utils_

utils for building and uploading Sphinx documentation

"""
import os
import sys
import tarfile

from fabric.operations import local
import pluggage.registry

from cirrus.configuration import load_configuration
from cirrus.logger import get_logger

LOGGER = get_logger()


def get_publisher_plugin(plugin_name):
    """
    _get_publisher_plugin_

    Get the publisher plugin requested from the factory
    """
    factory = pluggage.registry.get_factory(
        'publish',
        load_modules=['cirrus.plugins.publishers']
    )
    return factory(plugin_name)


def doc_artifact_name(config):
    """
    given cirrus config, build the expected doc artifact name
    """
    artifact_name = "{0}-{1}.tar.gz".format(
        config.package_name(),
        config.package_version()
    )
    doc_artifact = os.path.join(
        os.getcwd(),
        config['doc']['artifact_dir'],
        artifact_name
    )
    return doc_artifact


def build_docs(make_opts=None):
    """
    _build_docs_

    Runs 'make' against a Sphinx makefile.
    Requires the following cirrus.conf section:

    [doc]
    sphinx_makefile_dir = /path/to/makefile

    :param list make_opts: Options to run the Sphinx 'make' command gathered
        from the calling command's --docs option. If None or an empty list,
        'make' will be run using 'clean html'
    """
    LOGGER.info('Building docs')
    config = load_configuration()
    build_params = config.get('build', {})
    venv_name = build_params.get('virtualenv_name', 'venv')

    try:
        docs_root = os.path.join(
            os.getcwd(),
            config['doc']['sphinx_makefile_dir'])
    except KeyError:
        LOGGER.error(
            'Did not find a complete [doc] section in cirrus.conf'
            '\nSee below for an example:'
            '\n[doc]'
            '\nsphinx_makefile_dir = /path/to/sphinx')
        sys.exit(1)

    cmd = 'cd {} && make clean html'.format(docs_root)

    if make_opts:
        # additional args were passed after --docs. Pass these to make
        cmd = 'cd {} && make {}'.format(docs_root, ' '.join(make_opts))

    local('. ./{}/bin/activate && {}'.format(venv_name, cmd))
    LOGGER.info('Build command was "{}"'.format(cmd))


def build_doc_artifact():
    """
    build sphinx documentation and create an artifact to be uploaded to
    a remote server

    Requires the following cirrus.conf section:
    [doc]
    sphinx_makefile_dir = /path/to/makefile
    sphinx_doc_dir = /path/to/_build/docdir
    artifact_dir = /path/to/archive/dir
    """
    LOGGER.info("Building doc archive...")

    config = load_configuration()
    artifact_name = doc_artifact_name(config)
    arcname = os.path.basename(artifact_name).rsplit('.', 2)[0]
    doc_dir = config['doc']['sphinx_doc_dir']

    if not os.path.exists(doc_dir):
        msg = "Documentation path: {0} Not Found".format(doc_dir)
        LOGGER.error(msg)
        raise RuntimeError(msg)

    with tarfile.open(artifact_name, "w:gz") as tar:
        tar.add(doc_dir, arcname=arcname)

    LOGGER.info("Documentation artifact created at: {}".format(artifact_name))

    return artifact_name


def publish_documentation(opts):
    """
    Publish Sphinx documentation.

    If a tarfile exists for the current program version, that file will
    be used. Otherwise, the documentation will be built and packaged
    before uploading.

    Requires the publish_method plugin to be specified in the cirrus.conf [doc]
    section, and a section containing the required fields for the publisher
    method, e.g:
    [doc]
    publisher = file_server

    :param argparse.Namspace opts: A Namespace of publisher options
    """
    LOGGER.info("Preparing to upload documentation...")
    config = load_configuration()
    doc_params = config.get('doc', {})

    doc_artifact = doc_artifact_name(config)
    if not os.path.exists(doc_artifact):
        msg = 'Documentation tarball not found at {}'.format(doc_artifact)
        LOGGER.error(msg)
        raise RuntimeError(msg)

    try:
        publisher = doc_params['publisher']
    except KeyError:
        LOGGER.error(
            'Did not find a publisher in [doc] section of cirrus.conf'
            '\nSee below for an example:'
            '\n[doc]'
            '\npublisher = doc_file_server')
        sys.exit(1)

    plugin = get_publisher_plugin(publisher)

    if opts.test:
        LOGGER.info(
            "Uploading {}-{}.tar.gz to file server disabled by test or "
            "option...".format(
                config.package_name(), config.package_version()
            )
        )
        return

    plugin.publish(doc_artifact)
    return
