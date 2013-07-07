# -*- coding: utf-8 -*-

import cherrypy
from . import _tickets
from cherrybase.utils import to_int
from rco import client

class TicketAuth (cherrypy.Tool):

    cache_size = 10000

    def __init__(self):
        super (TicketAuth, self).__init__ (
            point = 'before_handler',
            callable = self.run,
            name = 'ticket_auth',
            priority = 50
        )

    def get_tickets (self):
        app = cherrypy.serving.request.app
        if not hasattr (app, 'service'):
            raise _tickets.AuthError ('ticket_auth tool can work with service only', -3100)
        if not hasattr (app.service, 'tickets'):
            app.service.tickets = {}
        return app.service.tickets

    def revoke (self, tid):
        tickets = self.get_tickets ()
        if tid in tickets:
            tickets [tid].valid = False
        if len (tickets) > self.cache_size:
            tickets.clear ()
            tickets.update ({_tid: ticket for _tid, ticket in tickets.items () if ticket.valid ()})

    def run (self, strict = True, callback_method = 'callbacks.auth.revoke'):
        request = cherrypy.serving.request
        tickets = self.get_tickets ()
        tid = request.headers.get ('RCO-Ticket')
        if not tid:
            if strict:
                raise _tickets.AuthError ('Show me your ticket', -3000)
            request.ticket = None
            return
        tid = tid.lower ()
        request.ticket = tickets.get (tid)
        if request.ticket:
            if not request.ticket.valid:
                request.ticket = None
                if strict:
                    raise _tickets.AuthError ('Invalid ticket', -3001)
            return
        try:
            request.ticket = _tickets.Ticket (
                tid,
                client.get_service ('logon').auth.register (
                    tid,
                    self.service.url (callback_method)
                )
            )
        except Exception as e:
            args = getattr (e, 'args', [None, 1])
            if len (args) < 2 or to_int (args [1], 1) != -3500:
                raise _tickets.AuthError ('Cannot check your ticket: {}'.format (e))





