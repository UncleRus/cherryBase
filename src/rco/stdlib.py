# -*- coding: utf-8 -*-

from cherrybase.rpc import expose
import cherrypy

class Keyring (object):

    def __init__ (self, security_manager):
        self._manager = security_manager

    @expose
    def keys (self):
        _own_key = cherrypy.serving.request.toolmaps ['tools'].get ('gpg_in', {})['key']
        result = {}
        for key in self._manager.gpg.list_keys ():
            if not key ['fingerprint'].endswith (_own_key):
                result [key ['fingerprint']] = key ['uids'][0] if len (key ['uids']) > 0 else None
        return result
