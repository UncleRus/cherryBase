# -*- coding: utf-8 -*-

import cherrypy
from cherrybase import db, orm

def use_orm (*args, **kwargs):
    return orm.use_orm ('test', *args, **kwargs)

def use_db (*args, **kwargs):
    return db.use_db ('test', *args, **kwargs)


import sqlalchemy.schema as sas

class RootController (object):

    @use_orm ()
    def __init__ (self, session):
        #metadata = session.
        #self.site_objects = sas.Table ('cp_site_objects', meta)
        print session

    @cherrypy.expose
    @cherrypy.tools.jinja (template = 'index.tpl')
    @use_db ()
    @use_orm ()
    def index (self, session, db, *args, **kwargs):
        app = cherrypy.request.app
        app.log.error ('***** SOME APP MESSAGE *****', 'test')
        db.select_all ('select * from cp_site_objects')
<<<<<<< HEAD
        print 'Raw output', session
=======
        print 'Raw output'
>>>>>>> refs/remotes/origin/master
        return {
            'who': 'world',
            'ami': 'test'
        }

    @cherrypy.expose
    def subpage (self, param1 = None, param2 = None):
        return 'param1: {}, param2: {}'.format (param1, param2)
