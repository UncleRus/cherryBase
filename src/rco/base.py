# -*- coding: utf-8 -*-

from cherrybase import rpc
import gnupg
import cherrypy
from . import stdlib

class SecurityError (Exception):
    pass


class Namespace (object):
    pass


class SecurityManager (object):

    def __init__ (self, gpg_homedir, gpg_key, gpg_password):
        self.gpg = gnupg.GPG (gnupghome = gpg_homedir)
        self.key = gpg_key
        self.password = gpg_password
        self.ifaces = {}

    def connect_interface (self, iface):
        if not isinstance (iface, CryptoInterface):
            raise ValueError ('Interface must be instance of rco.CryptoInterface')
        self.ifaces [iface._mount_point] = iface.system.methods.keys ()

    def can_execute (self, iface, client_key, method):
        # FIXME: Сделать нормальную проверку
        return True


class CryptoInterface (rpc.Controller):

    _cp_config = {
        'tools.xmlrpc.on': True,
        'tools.xmlrpc.allow_none': True,
        'tools.gpg_in.on': True,
        'tools.gpg_in.force': True,
        'tools.gpg_in.target_ct': 'text/xml',
        'tools.gpg_out.on': True,
    }

    def __init__ (self, security_manager, mount_point = '/'):
        self._mount_point = mount_point
        self._security = security_manager
        if mount_point == '/':
            self.control = Namespace ()
            self.control.keyring = stdlib.Keyring (self._security)
        super (CryptoInterface, self).__init__ ()
        self._security.connect_interface (self)

    def _call_method (self, method, name, args, vpath, parameters):
        if not self._security.can_execute (self, cherrypy.request._gpg_client_key, name):
            raise SecurityError ('Access denied', -1000)
        return super (CryptoInterface, self)._call_method (method, name, args, vpath, parameters)
