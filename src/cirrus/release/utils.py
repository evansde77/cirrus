import datetime
import os
import re

import pluggage.registry

from cirrus.configuration import load_configuration


def highlander(iterable):
    """check only single True value in iterable"""
    # There Can Be Only One!!!
    i = iter(iterable)
    return any(i) and not any(i)


def parse_version(version):
    """
    _parse_version_

    Parse semantic major.minor.micro version string

    :param version: X.Y.Z format version string

    :returns: dictionary containing major, minor, micro versions
    as integers

    """
    split = version.split('.', 2)
    return {
        'major': int(split[0]),
        'minor': int(split[1]),
        'micro': int(split[2]),
    }


def bump_version_field(version, field='major'):
    """
    parse the version and update the major, minor and micro
    version specified by field
    Return the updated version string
    """
    vers_params = parse_version(version)
    vers_params[field] += 1
    if field == 'major':
        vers_params['minor'] = 0
        vers_params['micro'] = 0
    elif field == 'minor':
        vers_params['micro'] = 0

    return "{major}.{minor}.{micro}".format(**vers_params)


def artifact_name(config):
    """
    given cirrus config, build the expected
    artifact name
    """
    a_name = "{0}-{1}.tar.gz".format(
        config.package_name(),
        config.package_version()
    )
    build_artifact = os.path.join(
        os.getcwd(),
        'dist',
        a_name
    )
    return build_artifact


def egg_artifact_name(config):
    """
    given cirrus config, build the expected
    artifact name
    """
    a_name = "{0}-{1}.tar.gz".format(
        config.package_name(),
        config.package_version()
    )
    build_artifact = os.path.join(
        os.getcwd(),
        'dist',
        a_name
    )
    return build_artifact


def wheel_artifact_name(config):
    """
    given cirrus config, build the expected
    artifact name
    """
    a_name = "{0}-{1}.tar.gz".format(
        config.package_name(),
        config.package_version()
    )
    build_artifact = os.path.join(
        os.getcwd(),
        'dist',
        a_name
    )
    return build_artifact


parse_to_list = lambda s: [x.strip() for x in s.split(',') if x.strip()]


def release_branch_name(config):
    """
    build expected release branch name from current config

    """
    branch_name = "{0}{1}".format(
        config.gitflow_release_prefix(),
        config.package_version()
    )
    return branch_name


def convert_bool(value):
    """helper to make sure bools are bools"""
    if value in (True, False):
        return value
    if value is None:
        return False
    if str(value).lower() in ('true', '1'):
        return True
    return False


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


def release_config(config, opts):
    """
    _release_config_

    Extract and validate the release config parameters
    from the cirrus config for the package
    """
    release_config_defaults = {
        'wait_on_ci': False,
        'wait_on_ci_develop': False,
        'wait_on_ci_master': False,
        'wait_on_ci_timeout': 600,
        'wait_on_ci_interval': 2,
        'push_retry_attempts': 1,
        'push_retry_cooloff': 0,
        'github_context_string': None,
        'update_github_context': False,
        'develop_github_context_string': None,
        'master_github_context_string': None,
        'update_develop_github_context': False,
        'update_master_github_context': False
    }

    release_conf = {}
    if 'release' not in config:
        release_conf = release_config_defaults
    else:
        for key, val in release_config_defaults.iteritems():
            release_conf[key] = config.get_param('release', key, val)

    release_conf['wait_on_ci'] = convert_bool(release_conf['wait_on_ci'])
    release_conf['wait_on_ci_develop'] = convert_bool(
        release_conf['wait_on_ci_develop']
    )
    release_conf['wait_on_ci_master'] = convert_bool(
        release_conf['wait_on_ci_master']
    )

    if opts.wait_on_ci:
        release_conf['wait_on_ci'] = True
    if opts.github_context_string:
        release_conf['update_github_context'] = True
        release_conf['github_context_string'] = opts.github_context_string

    if opts.github_develop_context_string:
        release_conf['update_develop_github_context'] = True
        release_conf['github_develop_context_string'] = opts.github_develop_context_string
    if opts.github_master_context_string:
        release_conf['update_master_github_context'] = True
        release_conf['github_master_context_string'] = opts.github_master_context_string

    # validate argument types
    release_conf['wait_on_ci_timeout'] = int(
        release_conf['wait_on_ci_timeout']
    )
    release_conf['wait_on_ci_interval'] = int(
        release_conf['wait_on_ci_interval']
    )
    release_conf['update_github_context'] = convert_bool(
        release_conf['update_github_context']
    )
    release_conf['push_retry_attempts'] = int(
        release_conf['push_retry_attempts']
    )
    release_conf['push_retry_cooloff'] = int(
        release_conf['push_retry_cooloff']
    )

    if release_conf['update_github_context']:
        # require context string
        if release_conf['github_context_string'] is None:
            msg = "if using update_github_context you must provide a github_context_string"
            raise RuntimeError(msg)
        release_conf['github_context_string'] = parse_to_list(
            release_conf['github_context_string']
        )
    if release_conf['update_develop_github_context']:
        # require context string
        # if release_conf['github_develop_context_string'] is None:
        if release_conf['github_develop_context_string'] is None:
            msg = "if using update_develop_github_context you must provide a github_context_string"
            raise RuntimeError(msg)
        release_conf['github_develop_context_string'] = parse_to_list(
            release_conf['github_develop_context_string']
        )
    if release_conf['update_master_github_context']:
        # require context string
        if release_conf['github_master_context_string'] is None:
            msg = "if using update_master_github_context you must provide a github_master_context_string"
            raise RuntimeError(msg)
        release_conf['github_master_context_string'] = parse_to_list(
            release_conf['github_master_context_string']
        )
    return release_conf


DEFAULT_FORMAT = "%Y%m%d"


def nightly_config(conf=None):
    """
    get the nightly config settings from
    the release section

    """
    result = {
        "nightly_format": DEFAULT_FORMAT,
        "nightly_separator": "-nightly-"
    }
    if not conf:
        conf = load_configuration()
    if not conf.has_section('release'):
        return result
    result['nightly_format'] = conf.get_param("release", "nightly_format", result['nightly_format'])
    result['nightly_separator'] = conf.get_param("release", "nightly_separator", result['nightly_separator'])
    return result


def is_nightly(version):
    """
    return True/False if the version string
    provided matches a nightly format.

    """
    conf = nightly_config()
    reg = "^[0-9]+\.[0-9]+\.[0-9]+{}".format(conf['nightly_separator'])
    matcher = re.compile(reg)
    elems = matcher.split(version, 1)
    if len(elems) == 2:
        return True
    return False


def new_nightly():
    """
    generate a new nightly version

    """
    cirrus_conf = load_configuration()
    nightly_conf = nightly_config(cirrus_conf)
    now = datetime.datetime.now()
    ts = now.strftime(nightly_conf['nightly_format'])
    current = cirrus_conf.package_version()

    nightly = "{version}{sep}{ts}".format(
        version=current,
        sep=nightly_conf['nightly_separator'],
        ts=ts
    )
    return nightly


def remove_nightly(ghc):
    """
    remove the nightly part from the cirrus.conf version
    """
    cirrus_conf = load_configuration()
    nightly_conf = nightly_config(cirrus_conf)
    current = cirrus_conf.package_version()
    if is_nightly(current):
        new_version = current.split(nightly_conf['nightly_separator'], 1)[0]
        cirrus_conf.update_package_version(new_version)
        ghc.commit_files_optional_push(
            "remove nightly tag from cirrus.conf",
            False,
            "cirrus.conf"
        )
    return