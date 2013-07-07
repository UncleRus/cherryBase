# -*- coding: utf-8 -*-

from cherrybase.rpc import expose
import cherrypy
from rco import BaseError


class KeyringError (BaseError):
    pass


class SecurityLib (object):

    def __init__ (self, security_manager):
        self._manager = security_manager


class Keyring (SecurityLib):

    @expose
    def keys (self):
        '''Get full list of public keys'''
        return self._manager.keys

    @expose
    def append (self, armored):
        '''Import key in armored package format'''
        return self._manager.import_keys (armored)

    @expose
    def remove (self, keys):
        '''Remove key(s)'''
        self._manager.delete_keys (keys)

    @expose
    def export (self, keys):
        '''Get key(s) in armored package format'''
        return self._manager.export_keys (keys)


class Access (SecurityLib):

    @expose
    def keys_rights (self, keys = None):
        '''Get rights of key(s)'''
        self._manager.rights (keys = keys)

    @expose
    def methods_rights (self, methods = None):
        '''Get rights of key(s)'''
        self._manager.rights (methods = methods)

    @expose
    def grant (self, methods, keys):
        '''Grant execution on method(s)/namespace(s) to key(s)'''
        self._manager.grant (methods, keys)

    @expose
    def revoke (self, methods, keys):
        '''Revoke execution on method(s)/namespace(s) from key(s)'''
        self._manager.revoke (methods, keys)


class Meta (SecurityLib):

    def __init__ (self, security_manager, code, version, title):
        super (Meta, self).__init__ (security_manager)
        self.code = code
        self.title = title
        self.version = version
        self.key = None

    def _own_key (self):
        app = cherrypy.request.app
        return app.service.service_config ('security.key', require = True)

    @expose
    def public_key (self):
        '''Public key of this service'''
        if not self.key:
            self.key = self._manager.gpg.export_keys (self._own_key ())
        return self.key

    @expose
    def info (self):
        '''Service description'''
        return {
            'code': self.code,
            'title': self.title,
            'version': self.version,
            'key_fingerprint': self._own_key ()
        }
