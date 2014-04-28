"""
_setup.py_

Cirrus template setup.py that reads most of its business
from the cirrus.conf file

"""
import setuptools
import ConfigParser

parser = ConfigParser.RawConfigParser()
parser.read('cirrus.conf')
src_dir = parser.get('package', 'find_packages')



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
    setup_args['packages'] = setuptools.find_packages(src_dir)
    setup_args['provides'] = setuptools.find_packages(src_dir)


setuptools.setup(**setup_args)

