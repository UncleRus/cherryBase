# -*- coding: utf-8 -*-

import cherrypy
from cherrybase import db

def use_db (*args, **kwargs):
    return db.use_db ('test', *args, **kwargs)

class RootController (object):

    @cherrypy.expose
    @cherrypy.tools.jinja (template = 'index.tpl')
    @use_db ()
    def index (self, db, *args, **kwargs):
        app = cherrypy.request.app
        app.log.error ('***** SOME APP MESSAGE *****', 'test')
        db.select_all ('select * from cp_site_objects')
        print 'Raw output'
        return {
            'who': 'world',
            'ami': 'test'
        }

    @cherrypy.expose
    def subpage (self, param1 = None, param2 = None):
        return 'param1: {}, param2: {}'.format (param1, param2)
