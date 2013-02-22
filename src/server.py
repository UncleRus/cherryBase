#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cherrybase, cherrypy, pkg_resources
from pprint import pprint

class RootController (object):

    @cherrypy.expose
    @cherrypy.tools.jinja (template = 'index.tpl')
    def default (self, *args, **kwargs):
        pprint (cherrypy.request.config)
        return {'who': 'world', 'ami': 'test'}


class RpcController (cherrybase.rpc.Controller):

    class Testlib (cherrybase.rpc.Controller):

        @cherrybase.rpc.expose
        def add (self, x, y):
            '''Сложить аргументы'''
            return x + y

    def __init__ (self):
        self.testlib = self.Testlib (False)
        super (RpcController, self).__init__ ()



if __name__ == '__main__':
    print pkg_resources.resource_filename ('app', 'config/debug.conf')
    server = cherrybase.app.Server (
        applications = [
            cherrybase.app.Application (
                name = 'test',
                routes = (('/', RootController (), None),),
                vhosts = ('test.cb.ru:8080', 'www.test.cb.ru:8080'),
                config = pkg_resources.resource_filename ('app', 'config/debug.conf')
            )
        ],
        config = None
    )
    print vars (server.applications [0])
    server.start ()
