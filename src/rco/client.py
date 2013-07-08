# -*- coding: utf-8 -*-

import xmlrpclib
import cherrybase.tools.gpg
from StringIO import StringIO
import cherrypy
from rco import BaseError
from . import base

class GpgTransport (xmlrpclib.Transport):

    user_agent = 'rco.client'

    def __init__ (self, gpg_homedir, gpg_key, gpg_password, gpg_server_key, headers = None, use_datetime = 0):
        xmlrpclib.Transport.__init__ (self, use_datetime)
        self.gpg_server_key = gpg_server_key
        self.gpg = cherrybase.tools.gpg.Encoder (gpg_homedir, gpg_key, gpg_password)
        self.headers = headers or {}

    def send_request (self, connection, handler, request_body):
        xmlrpclib.Transport.send_request (
            self,
            connection,
            '{}/{}'.format (handler.rstrip ('/'), self.gpg_server_key),
            request_body
        )

    def send_content (self, connection, request_body):
        # FIXME: Определять ACCEPT-ENCODING: gzip сервера и сжимать пост
        for header, value in self.headers.items ():
            if header not in ('Content-Type', 'Content-Length'):
                connection.putheader (header, value)
        connection.putheader ('Content-Type', 'application/pgp-encrypted')
        encoded = self.gpg.encode (request_body, self.gpg_server_key)
        connection.putheader ('Content-Length', str (len (encoded)))
        connection.endheaders (encoded)

    def parse_response (self, response):
        if hasattr (response, 'getheader') and \
                response.getheader ('Content-Encoding', '') == 'gzip':
            stream = xmlrpclib.GzipDecodedResponse (response)
        else:
            stream = response

        encoded = []
        while True:
            data = stream.read (1024)
            if self.verbose:
                print 'encoded body:', data
            if not data:
                break
            encoded.append (data)

        try:
            # Пробуем расшифровать
            return xmlrpclib.Transport.parse_response (
                self,
                StringIO (self.gpg.decode (u''.join (encoded), self.gpg_server_key).encode ('utf-8'))
            )
        except cherrybase.tools.gpg.GpgError:
            return xmlrpclib.Transport.parse_response (self, StringIO (u''.join (encoded).encode ('utf-8')))


class LookupError (BaseError):
    pass


# FIXME: Переделать под полноценный роутер
_routes = {
    'logon': ('http://logon.rco:8080/', '55A6F35DC05A3728FB45AA0277EA551D7EAC9ABD')
}


def lookup (service_name, version = None):
    if not cherrypy.request.app:
        raise LookupError ('Cannot lookup outside the request process', -4000)
    # FIXME: Кеширование ответов роутера
    if service_name in _routes:
        return _routes [service_name]
    raise LookupError ('Service "{}, {}" not found'.format (service_name, version), -4001)


def Server (uri, key, gpg_homedir = None, gpg_key = None, gpg_password = None, ticket = None):
    headers = {'RCO-Ticket': ticket} if ticket else None
    return xmlrpclib.Server (
        uri = uri,
        transport = GpgTransport (
            gpg_homedir = gpg_homedir or base.config ('security.homedir', strict = True),
            gpg_key = gpg_key or base.config ('security.key', strict = True),
            gpg_password = gpg_password or base.config ('security.password', strict = True),
            gpg_server_key = key,
            headers = headers
        ),
        allow_none = True
    )


def get_service (service_name, version = None):
    uri, key = lookup (service_name, version)
    return Server (uri, key)

