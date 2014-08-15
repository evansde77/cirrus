"""
_setup.py_

Cirrus template setup.py that reads most of its business
from the cirrus.conf file

"""
import os
import setuptools
import ConfigParser
from pip.req import parse_requirements


def get_default(parser, section, option, default):
    """helper to get config settings with a default if not present"""
    try:
        result = parser.get(section, option)
    except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
        result = default
    return result


def install_requires(reqs_file):
    """parse requirements file, return list of reqs suitable for install_requires"""
    result = [ str(req.req) for req in parse_requirements(reqs_file)]
    return result


parser = ConfigParser.RawConfigParser()
parser.read('cirrus.conf')
src_dir = get_default(parser, 'package', 'find_packages', '.')
excl_dirs = get_default(parser, 'package', 'exclude_packages', [])
reqs_file = get_default(parser, 'build', 'requirements_file', 'requirements.txt')


setup_args ={
    'name': parser.get('package', 'name'),
    'version': parser.get('package', 'version'),
    'description':parser.get('package', 'description')
}

if parser.has_section('console_scripts'):
    scripts = [
        '{0} = {1}'.format(opt,  parser.get('console_scripts', opt))
        for opt in parser.options('console_scripts')
    ]
    setup_args['entry_points'] = {'console_scripts' : scripts}

if src_dir:
    setup_args['packages'] = setuptools.find_packages(src_dir, exclude=excl_dirs)
    setup_args['provides'] = setuptools.find_packages(src_dir)

if os.path.exists(reqs_file):
    setup_args['install_requires'] = install_requires(reqs_file)

setuptools.setup(**setup_args)

