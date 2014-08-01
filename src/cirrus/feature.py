'''
_feature_

Command to create a new feature branch off of the develop branch
'''
from cirrus.configuration import load_configuration
from cirrus.git_tools import checkout_and_pull, branch

DEVELOP_BRANCH = 'develop'


def main():
    """
    _main_

    Execute feature command
    """
    config = load_configuration()
    feature_params = config.get('feature', {})
    local_repo = feature_params['local_repo']
    feature_name = feature_params['name']
    checkout_and_pull(local_repo, DEVELOP_BRANCH)
    branch(local_repo, feature_name, DEVELOP_BRANCH)
