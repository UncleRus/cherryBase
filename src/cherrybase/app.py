# -*- coding: utf-8 -*-
import cherrypy

class HandlerStub (object):
    pass

class ControllersTree (object):

    def __init__ (self, stub_class = HandlerStub):
        self.stub_class = stub_class
        self.clear ()

    def clear (self):
        self.root = None

    def controller_exists (self, path_list):
        if not path_list:
            return bool (self.root)
        current = self.root
        for element in path_list:
            try:
                current = getattr (current, element)
            except AttributeError:
                return False
        return True

    def find_owner (self, path_list):
        if not path_list and not self.root:
            self.root = self.stub_class ()
        result = self.root
        for element in path_list:
            if not hasattr (result, element):
                setattr (result, element, self.stub_class ())
            result = getattr (result, element)
        return result

    def add (self, path, controller, config = None):
        stripped_path = path.strip ('/')
        path_list = stripped_path.split ('/') if stripped_path else []

        if self.controller_exists (path_list):
            raise AttributeError ('Path "{0}" is busy'.format (path))

        if config:
            if hasattr (controller, '_cp_config') and isinstance (controller._cp_config, dict):
                controller._cp_config.update (config)
            else:
                controller._cp_config = config

        controller._mount_path = '/' + stripped_path
        if not path_list:
            self.root = controller
        else:
            setattr (self.find_owner (path_list [0:-1]), path_list [-1], controller)
        cherrypy.log.error ('{} is mounted on "{}"'.format (type (controller).__name__, path), 'TREE')

    def mount (self, mount_point, config = None):
        if not self.root:
            raise RuntimeError ('Nothing to mount')
        _config = {}
        if config:
            cherrypy._cpconfig.merge (_config, config)
        cherrypy.tree.mount (self.root, mount_point, _config)
