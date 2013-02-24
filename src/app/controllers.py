# -*- coding: utf-8 -*-

import cherrypy

class RootController (object):

    @cherrypy.expose
    @cherrypy.tools.jinja (template = 'index.tpl')
    def index (self, *args, **kwargs):
        return {
            'who': 'world',
            'ami': 'test'
        }

    @cherrypy.expose
    def subpage (self, param1 = None, param2 = None):
        return 'param1: {}, param2: {}'.format (param1, param2)
