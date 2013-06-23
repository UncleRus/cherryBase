# -*- coding: utf-8 -*-

from cherrybase import rpc
import gnupg
import cherrypy
import cherrybase
import pkg_resources
from cherrypy import _cpconfig
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

    def grant (self, methods, keys):
        # FIXME: Убрать заглушку
        pass

    def revoke (self, methods, keys):
        # FIXME: Убрать заглушку
        pass

    def keys (self, methods = None, keys = None):
        # FIXME: Убрать заглушку
        return {}

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
            self.control.access = stdlib.Access (self._security)
        super (CryptoInterface, self).__init__ ()
        self._security.connect_interface (self)

    def _call_method (self, method, name, args, vpath, parameters):
        if not self._security.can_execute (self, cherrypy.request._gpg_client_key, name):
            raise SecurityError ('Access denied', -1000)
        return super (CryptoInterface, self)._call_method (method, name, args, vpath, parameters)


class MetaInterface (rpc.Controller):

    _cp_config = {
        'tools.xmlrpc.on': True,
        'tools.xmlrpc.allow_none': True,
        'tools.gpg_in.on': False,
        'tools.gpg_out.on': False,
    }

    def __init__ (self, security_manager, code = None, version = None, title = None):
        self.meta = stdlib.Meta (security_manager, code, version, title)
        super (MetaInterface, self).__init__ ()


class Service (cherrybase.Application):

    def __init__ (self, package, basename, mode, vhosts, root = CryptoInterface):
        self.raw_config = {}
        _cpconfig.merge (
            self.raw_config,
            pkg_resources.resource_filename (package, '__config__/{}.conf'.format (mode))
        )
        self.security_manager = SecurityManager (
            self.raw_conf_val ('tools.gpg_in.homedir'),
            self.raw_conf_val ('tools.gpg_in.key'),
            self.raw_conf_val ('tools.gpg_in.password')
        )
        code = self.raw_conf_val ('service.code', package),
        super (Service, self).__init__ (
            name = code,
            vhosts = [vhost + basename if vhost [-1] == '.' else vhost for vhost in vhosts],
            config = self.raw_config,
            routes = (
                ('/', root (self.security_manager), None),
                (
                    '/meta',
                    MetaInterface (
                        self.security_manager,
                        code = code,
                        version = self.raw_conf_val ('service.version', '1.0.0'),
                        title = self.raw_conf_val ('service.title', code)
                    ),
                    None
                ),
            )
        )

    def raw_conf_val (self, entry, default = None, path = '/'):
        return self.raw_config.get (path, {}).get (entry, default)


