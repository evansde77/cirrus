"""
_templates_

"""
import os
import inspect


def find_template_dir():
    """util to locate this directory"""
    this_init = inspect.getsourcefile(find_template)
    return os.path.dirname(this_init)


def find_template(template_name):
    """util to find the path to a template file"""
    return os.path.join(
        find_template_dir(),
        template_name
    )
