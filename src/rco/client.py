# -*- coding: utf-8 -*-

import xmlrpclib
import cherrybase.tools.gpg
from StringIO import StringIO
import cherrypy

class GpgTransport (xmlrpclib.Transport):

    user_agent = 'rcolib'

    def __init__ (self, gpg_homedir, gpg_key, gpg_password, gpg_server_key, use_datetime = 0):
        xmlrpclib.Transport.__init__ (self, use_datetime)
        self.gpg_server_key = gpg_server_key
        self.gpg = cherrybase.tools.gpg.Encoder (gpg_homedir, gpg_key, gpg_password)

    def send_request (self, connection, handler, request_body):
        xmlrpclib.Transport.send_request (
            self,
            connection,
            '{}/{}'.format (handler.rstrip ('/'), self.gpg_server_key),
            request_body
        )

    def send_content (self, connection, request_body):
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

        return xmlrpclib.Transport.parse_response (
            self,
            StringIO (self.gpg.decode (u''.join (encoded), self.gpg_server_key).encode ('utf-8'))
        )


# FIXME: Переделать под полноценный роутер
_routes = {
    'logon': ('http://logon.rco:8080/', '55A6F35DC05A3728FB45AA0277EA551D7EAC9ABD')
}

_gpg_param = lambda x: cherrypy.serving.request.toolmaps ['tools'].get ('gpg_in', {})[x]


def lookup (service_name, version = None):
    if not cherrypy.request.app:
        raise RuntimeError ('Cannot lookup outside the request process')
    # FIXME: Один общий клиент для роутера на сервис для keep-alive
    # FIXME: Кеширование ответов роутера
    return _routes [service_name]


def Server (uri, key, gpg_homedir = None, gpg_key = None, gpg_password = None):
    return xmlrpclib.Server (
        uri = uri,
        transport = GpgTransport (
            gpg_homedir = gpg_homedir or _gpg_param ('homedir'),
            gpg_key = gpg_key or _gpg_param ('key'),
            gpg_password = gpg_password or _gpg_param ('password'),
            gpg_server_key = key
        ),
        allow_none = True
    )


def get_service (service_name, version = None):
    uri, key = lookup (service_name, version)
    return Server (uri, key)

