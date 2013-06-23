# -*- coding: utf-8 -*-

from cherrybase.rpc import expose
from cherrybase.utils import to_int
import cherrypy

_algos = {
    '0': None,
    '1': 'RSA',
    '2': 'RSA_E',
    '3': 'RSA_S',
    '16': 'ELGAMAL_E',
    '17': 'DSA',
    '16': 'ELGAMAL'
}


_get_own_key = lambda: cherrypy.serving.request.toolmaps ['tools'].get ('gpg_in', {})['key']


class KeyringError (Exception):
    pass


def _prepare_keys (keys):
    if isinstance (keys, basestring):
        keys = [keys]
    own_key = _get_own_key ()
    if own_key in keys:
        raise KeyringError ('Cannot manipulate my own key: {}'.format (own_key), -2000)
    return [k for k in keys if not k.endswith (own_key) and not own_key.endswith (k)]


def _check_gpg_result (result):
    if getattr (result, 'ok', False) or result:
        return
    raise KeyringError (
        '\n'.join ([line for line in getattr (result, 'stderr', 'gpg: {}'.format (getattr (result, 'status', 'Unknown error'))).splitlines () \
            if line.startswith ('gpg: ')]),
        - 2000
    )


class SecurityLib (object):

    def __init__ (self, security_manager):
        self._manager = security_manager


class Keyring (SecurityLib):

    @expose
    def keys (self):
        _own_key = _get_own_key ()
        result = {}
        for key in self._manager.gpg.list_keys ():
            if not key ['fingerprint'].endswith (_own_key):
                result [key ['fingerprint']] = {
                    'info': key ['uids'][0] if len (key ['uids']) > 0 else None,
                    'length': to_int (key ['length']),
                    'algo': _algos [key ['algo']]
                }
        return result

    @expose
    def append (self, armored):
        result = self._manager.gpg.import_keys (armored)
        return {res ['fingerprint']: (bool (to_int (res ['ok'])), res ['text'].strip ('\n')) for res in result.results}

    @expose
    def remove (self, keys):
        _check_gpg_result (self._manager.gpg.delete_keys (_prepare_keys (keys)))

    @expose
    def export (self, keys):
        return self._manager.gpg.export_keys (_prepare_keys (keys))


class Access (SecurityLib):

    @expose
    def grant (self, methods, keys):
        # FIXME: Убрать заглушку
        pass

    @expose
    def revoke (self, methods, keys):
        # FIXME: Убрать заглушку
        pass


class Meta (SecurityLib):

    def __init__ (self, security_manager, code, version, title):
        super (Meta, self).__init__ (security_manager)
        self.code = code
        self.title = title
        self.version = version
        self.key = None

    @expose
    def public_key (self):
        '''Public key of this service'''
        if not self.key:
            self.key = self._manager.gpg.export_keys (_get_own_key ())
        return self.key


    @expose
    def info (self):
        '''Service description'''
        return {
            'code': self.code,
            'title': self.title,
            'version': self.version,
            'key_fingerprint': _get_own_key ()
        }
