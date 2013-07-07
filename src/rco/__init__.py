# -*- coding: utf-8 -*-

class BaseError (Exception):

    def __init__ (self, message, code = 1):
        super (BaseError, self).__init__ (message, code)


from . import base, client
from base import CryptoInterface, MetaInterface, SecurityError, SecurityManager, Service


from cherrybase import utils as _utils
