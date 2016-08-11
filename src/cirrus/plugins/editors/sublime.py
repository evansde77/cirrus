#!/usr/bin/env python
"""
_sublime_

Editor plugin that creates a sublime project
file including a build rule for the cirrus
virtualenv

"""
import os
import inspect
import pystache

import cirrus.templates
from cirrus.editor_plugin import EditorPlugin
from cirrus.logger import get_logger


LOGGER = get_logger()


class Sublime(EditorPlugin):
    """
    Editor plugin that creates a sublime project
    for the repo.
    The project definition file includes
    a basic build system for the cirrus virtualenv.

    """
    @property
    def template(self):
        """return path to template"""
        templ_dir = os.path.dirname(inspect.getsourcefile(cirrus.templates))
        templ = os.path.join(templ_dir, 'sublime-project.mustache')
        return templ

    def setup(self, project_directory):
        """
        setup

        create a sublime project file from the template

        """
        package_name = self.config.package_name()
        project_name = "{}.sublime-project".format(package_name)
        project_file = os.path.join(project_directory, project_name)
        LOGGER.info("creating sublime project file: {}".format(project_name))
        context = {
            'repo_location': project_directory
        }

        pypaths = [project_directory]
        for subdir in self.opts.pythonpath:
            pypaths.append(os.path.join(project_directory, subdir))
        context['pythonpath'] = ':'.join(pypaths)

        with open(self.template, 'r') as handle:
            templ = handle.read()

        rendered = pystache.render(
            templ, context
            )
        with open(project_file, 'w') as handle:
            handle.write(rendered)
