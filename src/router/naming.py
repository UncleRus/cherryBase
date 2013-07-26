# -*- coding: utf-8 -*-

import sqlalchemy.schema as sas
import sqlalchemy.types as sat
from sqlalchemy.ext.declarative import declarative_base
from cherrybase import rpc, orm
import xmlrpclib
import cherrypy
import rco
import pkg_resources


BaseMdl = declarative_base ()


class NamingMdl (BaseMdl):

    __tablename__ = 'naming'

    url = sas.Column (sat.String (240), primary_key = True, nullable = False)
    code = sas.Column (sat.String (50), nullable = False)
    version = sas.Column (sat.String (50), nullable = False)
    fingerprint = sas.Column (sat.String (50), nullable = False)

    def __init__ (self, url, metainfo):
        self.url = url
        self.code = metainfo ['code']
        self.version = metainfo ['version']
        self.fingerprint = metainfo ['key_fingerprint']


def _use_orm (*args, **kwargs):
    return orm.use_orm (__package__, *args, **kwargs)


class NamingError (rco.BaseError):
    pass


class NamingLib (object):

    @_use_orm ()
    def __init__ (self, orm):
        BaseMdl.metadata.create_all (orm.bind)

    @rpc.expose
    @_use_orm ()
    def lookup (self, orm, service, version = None):
        '''
        Найти URL сервиса по его коду и версии
        '''
        version = pkg_resources.parse_version (version or '0.0.0')
        result = []
        for obj in orm.query (NamingMdl).filter (NamingMdl.code == service).all ():
            if pkg_resources.parse_version (obj.version) >= version:
                result.append ([obj.url, obj.fingerprint, obj.version])
        return result

    @rpc.expose
    @_use_orm ()
    def register (self, orm, url):
        '''
        Зарегистрировать сервис по указанному URL
        '''
        orm.query (NamingMdl).filter (NamingMdl.url == url).delete ()
        obj = NamingMdl (url, xmlrpclib.Server (uri = url + 'meta/', allow_none = True).meta.info ())
        if not obj.fingerprint.upper ().endswith (cherrypy.request.rco_client):
            raise NamingError ('Client key must be identical to service key', -5000)
        orm.add (obj)

    @rpc.expose
    @_use_orm ()
    def unregister (self, orm, url):
        '''
        Удалить регистрацию сервиса с указанным URL
        '''
        obj = orm.query (NamingMdl).filter (NamingMdl.url == url).first ()
        if not obj:
            return
        if not obj.fingerprint.upper ().endswith (cherrypy.request.rco_client):
            raise NamingError ('Client key must be identical to service key', -5000)
        orm.delete (obj)


