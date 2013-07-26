# -*- coding: utf-8 -*-

from cherrypy.process.plugins import SimplePlugin
from cherrypy.process.wspbus import states
from cherrybase.utils import to_int
import cherrypy
import threading
import logging
import time
import sys
from . import security, _xmlrpclib


class StarterStopper (SimplePlugin):
    '''
    Плагин, имеющий две коллекции callable: on_start и on_stop.
    Функции из on_start выполняются в отдельном потоке сразу после запуска шины.
    Функции из on_stop выполняются в основном потоке в процессе остановки шины.
    Плагин доступен как cherrypy.engine.starter_stopper.
    '''

    def __init__ (self, bus):
        super (StarterStopper, self).__init__ (bus)
        self.thread = None
        self.on_start = []
        self.on_stop = []

    def start (self):
        if not self.thread:
            self.thread = threading.Thread (target = self.run)
            self.thread.start ()

    def stop (self):
        if self.thread:
            self.thread.join ()
            self.thread = None
        for task in self.on_stop:
            task ()
        self.bus.log ('Stopper succesfully worked')

    def run (self):
        self.bus.publish ('acquire_thread')

        while self.bus.state == states.STARTING:
            time.sleep (0.1)

        if self.bus.state == states.STARTED:
            for task in self.on_start:
                task ()
            self.bus.log ('Starter succesfully worked')
        else:
            self.bus.log ('Wrong bus state, starter tasks ignored', logging.WARNING)

        self.bus.publish ('release_thread')


class EncryptedXmlrpcTool (cherrypy.Tool):
    '''
    Инструмент для замены tools.xmlrpc в криптоинтерфейсах.
    '''

    def __init__ (self):
        super (EncryptedXmlrpcTool, self).__init__ (
            point = 'before_handler',
            callable = self.run,
            name = 'encrypted_xmlrpc',
            priority = 10
        )

    def _wrapper (self):
        self._on_error (**self._merged_args ())

    def _setup (self):
        cherrypy.serving.request.error_response = self._wrapper
        super (EncryptedXmlrpcTool, self)._setup ()

    def run (self):
        request = cherrypy.serving.request
        request.rco_security = request.app.service.security_manager

        path = request.path_info.strip ('/')
        request.rco_client = path [path.rfind ('/') + 1:].upper ()
        if not request.rco_security.public_key_exists (request.rco_client):
            raise security.SecurityError ('Unknown client key', -1001)

        request.rco_encrypted = request.body.read ()
        request.rco_decrypted = request.rco_security.decrypt (request.rco_encrypted, request.rco_client).encode ('utf-8')
        request.rco_encrypt_response = True


    def _on_error (self):
        e = sys.exc_info ()[1]
        if hasattr (e, 'args') and len (e.args) > 1:
            message = unicode (e.args [0])
            code = to_int (e.args [1], 1)
        else:
            message = '{}: {}'.format (type (e).__name__, unicode (e))
            code = 1
        body = _xmlrpclib.dumps (
            _xmlrpclib.Fault (code, message),
            methodresponse = 1,
            encoding = 'utf-8',
            allow_none = True
        )

        request = cherrypy.request
        response = cherrypy.response
        response.status = '200 OK'

        if getattr (request, 'rco_encrypt_response', False):
            ct = 'application/pgp-encrypted'
            body = request.rco_security.encrypt (body, request.rco_client).encode ('utf-8')
        else:
            ct = 'text/xml'

        response.headers ['Content-Type'] = ct
        response.headers ['Content-Length'] = len (body)
        response.body = body

