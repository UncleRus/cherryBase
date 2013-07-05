# -*- coding: utf-8 -*-

from cherrybase.rpc import expose
from cherrybase import utils
import cherrypy
import time
from . import base, client

class AuthError (Exception):
    pass


class Ticket (object):

    def __init__ (self, tid, data = {}):
        self.tid = tid
        self.login = data.get ('login')
        self.expire = data.get ('expire')
        self.data = data.get ('data', {})
        self._valid = True

    @property
    def valid (self):
        return self._valid and self.expire - int (time.time ()) > 0

    @valid.setter
    def valid (self, value):
        self._valid = value


class CallbackLib (object):

    def __init__ (self, manager):
        self._manager = manager

    @expose
    def revoke (self, tid):
        '''Auth ticket revoke callback'''
        self._manager.revoke (tid)


class AuthManager (object):

    def __init__ (self, service):
        self.tickets = {}
        self.service = service
        self.service.auth_manager = self
        if not hasattr (self.service.tree.root, 'callbacks'):
            self.service.tree.root.callbacks = base.Namespace ()
        if not hasattr (self.service.tree.root.callbacks, 'auth'):
            lib = CallbackLib (self)
            self.service.tree.root.callbacks.auth = lib
            self.service.tree.root.system.methods ['callbacks.auth.revoke'] = lib.revoke.__doc__

    def revoke (self, tid):
        if tid in self.tickets:
            self.tickets [tid].valid = False

    def get_ticket (self, strict = True):
        tid = cherrypy.request.headers.get ('RCO-Ticket')
        if not tid:
            if strict:
                raise AuthError ('Show me your ticket', -3000)
            return None
        else:
            tid = tid.lower ()
            if tid in self.tickets:
                ticket = self.tickets [tid]
                if not ticket.valid:
                    if strict:
                        raise AuthError ('Invalid ticket', -3001)
                    return None
            else:
                # Регистрируем тикет
                try:
                    return Ticket (tid, client.get_service ('logon').auth.register (tid, self.service.url ('callbacks.auth.revoke')))
                except Exception as e:
                    args = getattr (e, 'args', [None, 1])
                    if len (args) < 2 or utils.to_int (args [1], 1) != -3500:
                        raise
                    if not strict:
                        return None
                    raise AuthError ('Invalid ticket', -3001)


def use_ticket (strict = True, position = 1):
    def _wrap (func):
        def _wrapped (*args, **kwargs):
            app = cherrypy.request.app
            ticket = app.service.auth_manager.get_ticket (strict)
            largs = list (args)
            largs.insert (position, ticket)
            return func (*largs, **kwargs)
    return _wrap

