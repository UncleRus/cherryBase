# -*- coding: utf-8 -*-

class BaseError (Exception):

    def __init__ (self, message, code = 1):
        super (BaseError, self).__init__ (message, code)


from cherrypy.lib import xmlrpcutil
_xmlrpclib = xmlrpcutil.get_xmlrpclib ()

from . import base, client, tickets, security, tools, naming
from base import CryptoInterface, MetaInterface, Service, Namespace

import cherrypy
toolbox = cherrypy.tools

toolbox.encrypted_xmlrpc = tools.EncryptedXmlrpcTool ()

cherrypy.engine.starter_stopper = tools.StarterStopper (cherrypy.engine)
cherrypy.config.update ({
    'engine.starter_stopper.on': True,
    'engine.task_manager.on': True
})
