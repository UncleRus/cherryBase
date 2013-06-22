# -*- coding: utf-8 -*-

import xmlrpclib
import cherrybase.tools.gpg
from StringIO import StringIO

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
