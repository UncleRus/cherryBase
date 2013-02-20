#!/usr/bin/python
# -*- coding: utf-8 -*-

import cherrypy
import cherrybase
# import jinja2
import pkg_resources
import cherrybase.db as db
from cherrybase.tools.auth import AuthController

class RootController (object):

    @cherrypy.expose
    @cherrypy.tools.jinja (template = 'index.tpl')
    @db.use_db ()
    def default (self, db, *args, **kwargs):
        self.test ()
        return {'who': 'world', 'ami': 'test'}

    @db.use_db ('cherry')
    def test (self, db):
        print db.select_all ('select * from cp_routes order by path')


class RpcController (cherrybase.rpc.Controller):

    class Testlib (cherrybase.rpc.Controller):

        @cherrybase.rpc.expose
        def add (self, x, y):
            '''Сложить аргументы'''
            return x + y

    def __init__ (self):
        super (RpcController, self).__init__ (auto_introspection = True)
        self.testlib = self.Testlib (False)

if __name__ == '__main__':
    tree = cherrybase.ControllersTree ()

    db.catalog ['default'] = db.drivers.PgSql (password = '123')
    db.catalog ['cherry'] = db.drivers.PgSql (password = '123', dbname = 'cherrypack')

    tree.add ('/', RootController ())
    tree.add ('/rpc', RpcController ())
    tree.add ('/auth', AuthController ())

    tree.mount ('/', pkg_resources.resource_filename ('app', 'config/debug.conf'))

    cherrybase.engine.start_engine ()
