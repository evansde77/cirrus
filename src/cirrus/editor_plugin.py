#!/usr/bin/env python
"""
editor_plugin

Base Plugin for setting up an editor project in a cirrus repo

"""
from pluggage.factory_plugin import PluggagePlugin

from cirrus.configuration import load_configuration


class EditorPlugin(PluggagePlugin):
    """
    base class for an editor plugin.
    Subclasses should override the setup method
    to create the editor IDE template/config

    """
    PLUGGAGE_FACTORY_NAME = 'editors'

    def __init__(self):
        super(EditorPlugin, self).__init__()
        self.config = None
        self.opts = None

    def run(self, opts):
        """
        _run_

        Run the plugin, calling the overloaded parser
        and setup methods
        """
        self.opts = opts
        project_dir = opts.repo
        self.config = load_configuration()
        self.setup(project_dir)

    def setup(self, project_directory):
        """
        _setup_

        :param project_directory: Location to set up project
        for the editor or IDE supported by this plugin

        """
        msg = "{}.setup is not implemented".format(type(self).__name__)
        raise NotImplementedError(msg)
