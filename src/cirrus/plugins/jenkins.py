import requests
from cirrus.configuration import get_buildserver_auth
from cirrus.logger import get_logger

LOGGER = get_logger()


class JenkinsClient(object):
    """Barebones Jenkins remote API wrapper"""

    def __init__(self, jenkins_url):
        self.jenkins_url = jenkins_url
        self.session = requests.Session()
        self.session.auth = get_buildserver_auth()

    def start_job(self, name, params):
        """
        Submit a build job.
        :param name: job name
        :param params: dictionary of build parameters
        :return: requests.Response object
        """
        url = '{}/job/{}/buildWithParameters'.format(self.jenkins_url, name)
        response = self.session.post(url, params=params)
        LOGGER.info('Submitting job to jenkins: {}'.format(response.url))
        return response
