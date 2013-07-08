# -*- coding: utf-8 -*-

import cherrypy
from cherrybase.utils import to_int
from rco import BaseError, client
import time
import logging


_max_cache_size = 10000


class AuthError (BaseError):
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


def _get_tickets ():
    app = cherrypy.serving.request.app
    if not hasattr (app, 'service'):
        raise AuthError ('tickets can work with service only', -3100)
    if not hasattr (app.service, 'tickets'):
        app.service.tickets = {}
    return app.service.tickets


def _check_ticket (strict, revoke_callback):
    request = cherrypy.serving.request
    tickets = _get_tickets ()
    tid = request.headers.get ('RCO-Ticket')
    if not tid:
        if strict:
            raise AuthError ('Show me your ticket', -3000)
        request.rco_ticket = None
        return
    tid = tid.lower ()
    request.rco_ticket = tickets.get (tid)
    if request.rco_ticket:
        if not request.rco_ticket.valid:
            request.rco_ticket = None
            if strict:
                raise AuthError ('Invalid ticket', -3001)
        return
    try:
        request.rco_ticket = Ticket (
            tid,
            client.get_service ('logon').auth.register (
                tid,
                request.app.service.url (revoke_callback)
            )
        )
    except Exception as e:
        request.app.log ('Cannot check ticket {}'.format (tid), 'RCO.AUTH', severity = logging.ERROR, traceback = True)
        args = getattr (e, 'args', [None, 1])
        if len (args) < 2 or to_int (args [1], 1) != -3500:
            raise AuthError ('Cannot check your ticket: {}'.format (e))
        if strict:
            raise AuthError ('Invalid ticket', -3001)


def revoke (tid):
    tickets = _get_tickets ()
    if tid in tickets:
        tickets [tid].valid = False
    if len (tickets) > _max_cache_size:
        tickets.clear ()
        tickets.update ({_tid: ticket for _tid, ticket in tickets.items () if ticket.valid ()})


def use (strict = True, revoke_callback = 'callback.auth.revoke'):
    def wrap (method):
        def wrapped (*args, **kwargs):
            _check_ticket (strict, revoke_callback)
            return method (*args, **kwargs)
        return wrapped
    return wrap

