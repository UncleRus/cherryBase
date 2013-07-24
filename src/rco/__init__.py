# -*- coding: utf-8 -*-

class BaseError (Exception):

    def __init__ (self, message, code = 1):
        super (BaseError, self).__init__ (message, code)


from . import base, client, tickets
from base import CryptoInterface, MetaInterface, SecurityError, SecurityManager, Service, Namespace

import cherrypy
toolbox = cherrypy.tools

