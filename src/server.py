#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cherrybase, cherrypy, pkg_resources

class MainController (object):

    @cherrypy.expose
    def default (self, *args, **kwargs):
        return u'Это типа сайт без вхостинга'

class RootController (object):

    @cherrypy.expose
    @cherrypy.tools.jinja (template = 'index.tpl')
    def index (self, *args, **kwargs):
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
    test = cherrybase.Application (
        name = 'test',
        vhosts = ('test.cb.ru:8080', 'www.test.cb.ru:8080'),
        config = pkg_resources.resource_filename ('app', 'config/debug.conf')
    )
    test.tree.add ('/', RootController ())

    server = cherrybase.Server (
        applications = [test],
        config = None,
        root_factory = MainController
    )
    server.start ()
