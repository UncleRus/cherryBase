# -*- coding: utf-8 -*-

import cherrypy
from cherrypy._cptools import ErrorTool
from cherrypy.lib import xmlrpcutil
import inspect
import sys
from . import utils

def _on_error (*args, **kwargs):
    e = sys.exc_info ()[1]
    if hasattr (e, 'args') and len (e.args) > 1:
        message = e.args [0]
        code = utils.to_int (e.args [1], 1)
    else:
        message = str (e)
        code = 1
    xmlrpclib = xmlrpcutil.get_xmlrpclib ()
    xmlrpcutil._set_response (xmlrpclib.dumps (xmlrpclib.Fault (code, message)))

cherrypy.tools.xmlrpc = ErrorTool (_on_error)


def expose (entity):
    entity.__rpc_exposed = True
    return entity


class Introspection (object):
    '''
    Класс RPC-библиотеки, обспечивающей интроспекцию (system)
    '''
    def __init__ (self, controller):
        self._controller = controller
        self.methods = {}

    def scan (self, obj = None, path = ''):
        _obj = obj if obj else self._controller
        for member in inspect.getmembers (_obj):
            if member [0].startswith ('_') or inspect.isclass (member [1]):
                continue
            _path = '.'.join ((path, member [0])) if path else member [0]
            if getattr (member [1], '__rpc_exposed', False):
                self.methods [_path] = member [1].__doc__
            elif not inspect.ismethod (member [1]):
                self.scan (member [1], _path)

    @expose
    def listMethods (self):
        '''This method returns a list of the methods the server has, by name.'''
        return sorted (self.methods.keys ())

    @expose
    def methodSignature (self, method):
        '''This method returns a description of the argument format a particular method expects.'''
        return 'undef'

    @expose
    def methodHelp (self, method):
        '''This method returns a text description of a particular method.'''
        if method not in self.methods:
            raise Exception ('Unknown method "{0}"'.format (method))
        return self.methods [method] if self.methods [method] else ''


class Controller (object):
    '''
    Базовый класс контроллеров RPC-библиотек
    '''
    _cp_config = {'tools.xmlrpc.on': True}

    def __init__ (self, introspection_factory = Introspection):
        if introspection_factory:
            self.system = introspection_factory (self)
            self.system.scan ()

    def _find_method (self, name):
        result = self
        for attr in str (name).split ('.'):
            result = getattr (result, attr, None)
            if not result:
                return None
        return result if getattr (result, '__rpc_exposed', False) else None

    def default (self, *vpath, **params):
        '''Обработчик по умолчанию'''
        cherrypy.request.body.fp.bytes_read = 0
        rpc_params, rpc_method = xmlrpcutil.process_body ()
        if rpc_method == 'ERRORMETHOD':
            raise Exception ('Invalid request', -32700)

        method = self._find_method (rpc_method)
        if method:
            body = method (*rpc_params, **params)
        else:
            raise Exception ('Method "{}" not found'.format (rpc_method), -32601)

        conf = cherrypy.serving.request.toolmaps ['tools'].get ('xmlrpc', {})
        xmlrpcutil.respond (
            body,
            conf.get ('encoding', 'utf-8'),
            conf.get ('allow_none', 0)
        )
        return cherrypy.serving.response.body
    default.exposed = True
