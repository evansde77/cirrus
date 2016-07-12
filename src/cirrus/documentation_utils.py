#!/usr/bin/env python
"""
_documentation_utils_

utils for building and uploading Sphinx documentation

"""
import json
import os
import sys
import tarfile

from fabric.operations import local
from requests_toolbelt import MultipartEncoder
import pluggage.registry

from cirrus.configuration import load_configuration
from cirrus.logger import get_logger
from cirrus.plugins.jenkins import JenkinsClient

LOGGER = get_logger()


def get_plugin(plugin_name):
    """
    _get_plugin_

    Get the deploy plugin requested from the factory
    """
    factory = pluggage.registry.get_factory(
        'upload',
        load_modules=['cirrus.plugins.uploaders']
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
        docs_root = os.path.join(os.getcwd(),
                                 config['doc']['sphinx_makefile_dir'])
    except KeyError:
        LOGGER.error('Did not find a complete [doc] section in cirrus.conf'
                     '\nSee below for an example:'
                     '\n[doc]'
                     '\n;sphinx_makefile_dir = /path/to/sphinx')
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
        tar.add(doc_dir, arcname=arcname, recursive=False)

    LOGGER.info("Documentation artifact created at: {}".format(artifact_name))

    return artifact_name


def upload_documentation(opts):
    """
    Upload Sphinx documentation to a remote server.

    If a tarfile exists for the current program version, that file will
    be used. Otherwise, the documentation will be built and packaged
    before uploading.

    The argparse.Namespace that calls this functions should have an
    option named '--docs' which takes a list of arguments which specify
    how the documentation should be built. If no arguments are provided,
    that indicates the documentation artifact already exists for the
    release version being uploaded or that the default arguments -
    'clean html' - should be used to create the documentation.

    Requires the following cirrus.conf section:
    [doc]
    upload_method = [file_server | jenkins]

    :param argparse.Namspace opts: A Namespace of upload options
    """
    LOGGER.info("Preparing to upload documentation...")
    config = load_configuration()
    doc_params = config.get('doc', {})

    doc_artifact = doc_artifact_name(config)
    if not os.path.exists(doc_artifact):
        msg = 'Documentation tarball not found at {}'.format(doc_artifact)
        LOGGER.error(msg)
        raise RuntimeError(msg)

    # make sure there is a valid upload method
    if not doc_params.get('upload_method') \
            or doc_params.get('upload_method') not in ['file_server', 'jenkins']:
        msg = 'Unknown upload method {}! Cannot upload documentation'.format(
            doc_params.get('upload_method')
        )
        LOGGER.error(msg)
        raise RuntimeError(msg)

    if doc_params['upload_method'] == 'file_server':
        # direct upload to a file server
        _file_server_upload(opts, config, doc_artifact)

    if doc_params['upload_method'] == 'jenkins':
        # pass doc artifact to a Jenkins job
        _jenkins_upload(opts, config, doc_artifact)


def _file_server_upload(opts, config, doc_artifact):
    """
    upload doc artifact via fabric put to file server

    .. warning:: If a file of the same name already exists in upload
        directory it will be overwritten without warning

    cirrus.conf [doc] section requires:
    upload_method = file_server
    file_server_upload_path = /path/to/upload/dir
    """
    plugin = get_plugin('file_server')

    if opts.test:
        LOGGER.info(
            "Uploading {}-{}.tar.gz to file server disabled by test or "
            "option...".format(
                config.package_name(), config.package_version()
            )
        )
        return
    plugin.upload(opts, doc_artifact)
    return


def _jenkins_upload(opts, config, doc_artifact):
    """
    pass the doc artifact to a Jenkins job. The actions performed by
    the Jenkins job is up to the user to decide. Suggested use of the
    Jenkins upload option is to pass the artifact to Jenkins, upload it
    to a server and unpack the files so they can be served from a webpage.

    Requires the following sections and values in cirrus.conf:

    [doc]
    upload_method = jenkins

    [jenkins]
    url = http://localhost:8080
    doc_job = default
    doc_var = archive
    arc_var = ARCNAME
    extra_vars = [
        {"name": varname, "value": varvalue},
        {"name": varname1, "value": varvalue1}
    ]

    .. note:: The doc_var is the location of the archive in the Jenkins
        workspace. It must match whatever is in the section "File location"
        in the Jenkins job configuration.

    .. note:: arc_var is the variable that will be used to name the file/folder
        the archive should be unpacked to as determined by the name of the
        archive filename. I.e. package-0.0.0.tar.gz => package-0.0.0

    .. note:: extra_vars is a list of dicts containing any other variables
        necessary for the Jenkins build.
    """
    try:
        jenkins_config = config['jenkins']
    except KeyError:
        msg = (
            '[jenkins] section missing from cirrus.conf. '
            'Please see below for an example.\n'
            '\n [jenkins]'
            '\n url = http://localhost:8080'
            '\n doc_job = default'
            '\n doc_var = archive'
            '\n arc_var = ARCNAME'
            '\n extra_vars = ['
            '\n    {"name": varname, "value": varvalue},'
            '\n    {"name": varname1, "value": varvalue1}'
            '\n ]'
        )
        raise RuntimeError(msg)

    filename = os.path.basename(doc_artifact)
    build_params = {
        "parameter": [
            {"name": jenkins_config['doc_var'], "file": "file0"}
        ]
    }

    if jenkins_config.get('arc_var'):
        arcname = filename.rsplit('.', 2)[0]
        build_params['parameter'].extend(
            {"name": jenkins_config['arc_var'], "value": arcname}
        )

    if jenkins_config.get('extra_vars'):
        build_params['parameter'].extend(jenkins_config['extra_vars'])

    payload = MultipartEncoder(
        fields={
            "file0": (filename, open(filename, 'rb'), 'application/x-gzip'),
            "json": json.dumps(build_params)
        }
    )

    if opts.test:
        LOGGER.info(
            "Uploading {}-{}.tar.gz to Jenkins disabled by test or "
            "option...".format(
                config.package_name(), config.package_version()
            )
        )
        return

    client = JenkinsClient(jenkins_config['url'])

    response = client.start_job_file_upload(jenkins_config['doc_job'], payload)

    if response.status_code != 201:
        LOGGER.error(response.text)
        raise RuntimeError(
            'Jenkins HTTP API returned code {}'.format(response.status_code)
        )
