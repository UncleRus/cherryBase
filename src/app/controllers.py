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
        metadata = sas.MetaData (bind = session.bind)
        self.site_objects = sas.Table ('cp_site_objects', metadata, autoload = True)

    @cherrypy.expose
    @cherrypy.tools.jinja (template = 'index.tpl')
    @use_db ()
    @use_orm ()
    def index (self, session, db, *args, **kwargs):
        app = cherrypy.request.app
        app.log.error ('***** SOME APP MESSAGE *****', 'test')
        db.select_all ('select * from cp_site_objects')
        for so in session.query (self.site_objects).order_by (self.site_objects._columns.rn):
            print so

        print 'Raw output', session
        return {
            'who': 'world',
            'ami': 'test'
        }

    @cherrypy.expose
    def subpage (self, param1 = None, param2 = None):
        return 'param1: {}, param2: {}'.format (param1, param2)
