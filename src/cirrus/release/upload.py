import os

from cirrus.configuration import load_configuration
from cirrus.release.utils import artifact_name, get_plugin
from cirrus.logger import get_logger

LOGGER = get_logger()


def upload_release(opts):
    """
    _upload_release_
    """
    LOGGER.info("Uploading release...")
    config = load_configuration()

    build_artifact = artifact_name(config)
    LOGGER.info("Uploading artifact: {0}".format(build_artifact))
    print(os.path.exists)
    if not os.path.exists(build_artifact):
        msg = (
            "Expected build artifact: {0} Not Found, upload aborted\n"
            "Did you run git cirrus release build?"
        ).format(build_artifact)
        LOGGER.error(msg)
        raise RuntimeError(msg)

    # merge in release branches and tag, push to remote
    tag = config.package_version()
    LOGGER.info("Loading plugin {}".format(opts.plugin))
    plugin = get_plugin(opts.plugin)

    if opts.test:
        LOGGER.info("Uploading {} to pypi disabled by test or option...".format(tag))
        return

    plugin.upload(opts, build_artifact)
    return

