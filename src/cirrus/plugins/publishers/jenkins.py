#!/usr/bin/env python
"""
_jenkins_

Publisher plugin that uses jenkins to handle publishing documentation

"""
import json

from requests_toolbelt import MultipartEncoder

from cirrus.logger import get_logger
from cirrus.plugins.jenkins import JenkinsClient
from cirrus.publish_plugins import Publisher

LOGGER = get_logger()


class Documentation(Publisher):
    PLUGGAGE_OBJECT_NAME = 'jenkins'

    def publish(self, opts, doc_artifact):
        """
        Pass the doc artifact to a Jenkins job. The actions performed by
        the Jenkins job is up to the user to decide. Suggested use of the
        Jenkins upload option is to pass the artifact to Jenkins, upload it
        to a server and unpack the files so they can be served from a webpage.

        Requires the following sections in cirrus.conf:

        [doc]
        publisher = jenkins

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
            jenkins_config = self.package_conf['jenkins']
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
                {"name": jenkins_config['doc_var'], "file": "file0"}]}

        if jenkins_config.get('arc_var') is not None:
            arcname = filename.rsplit('.', 2)[0]
            build_params['parameter'].extend(
                {"name": jenkins_config['arc_var'], "value": arcname})

        if jenkins_config.get('extra_vars') is not None:
            build_params['parameter'].extend(jenkins_config['extra_vars'])

        payload = MultipartEncoder(
            fields={
                "file0": (filename, open(filename, 'rb'), 'application/x-gzip'),
                "json": json.dumps(build_params)})

        client = JenkinsClient(jenkins_config['url'])

        response = client.start_job_file_upload(jenkins_config['doc_job'], payload)

        if response.status_code != 201:
            LOGGER.error(response.text)
            raise RuntimeError(
                'Jenkins HTTP API returned code {}'.format(response.status_code)
            )
