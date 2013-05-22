# -*- coding: utf-8 -*-

import gnupg, os
import cherrypy
from cherrypy._cptools import Tool, HandlerWrapperTool
from cherrypy._cpcompat import ntou
from cherrypy._cpreqbody import RequestBody, SizedReader
from cStringIO import StringIO


class ExtGPG (gnupg.GPG):
    '''
    Расширение класса gnupg.GPG
    '''
    def decrypt_verify_file (self, file, encoder_key, always_trust = False, passphrase = None, output = None):
        args = ["--decrypt", "-u", encoder_key]
        if output:
            if os.path.exists (output):
                os.remove (output)
            args.append ('--output "%s"' % output)
        if always_trust:
            args.append ("--always-trust")
        result = self.result_map ['crypt'](self)
        self._handle_io (args, file, result, passphrase, binary = True)
        gnupg.logger.debug ('decrypt result: %r', result.data)
        return result

    def decrypt_verify (self, message, encoder_key, **kwargs):
        data = gnupg._make_binary_stream (message, self.encoding)
        result = self.decrypt_verify_file (data, encoder_key, **kwargs)
        data.close ()
        return result


class Encoder (object):
    '''
    Обертка для GPG
    '''
    def __init__ (self, homedir, key_fingerprint, key_password):
        self._key = key_fingerprint
        self._password = key_password
        self._gpg = ExtGPG (gnupghome = homedir)
        # self._gpg.verbose = True

    def _check_result (self, result):
        if getattr (result, 'ok', False):
            return
        raise RuntimeError ('\n'.join ([line for line in getattr (result, 'stderr', 'gpg: {}'.format (getattr (result, 'status', 'Unknown error'))).splitlines () if line.startswith ('gpg: ')]))

    def public_key_exists (self, key):
        if len (key) < 8:
            return False
        key = key.upper ()
        for item in self._gpg.list_keys ():
            if item.get ('fingerprint', '').upper ().endswith (key):
                return True
        return False

    def encode (self, data, recipient_key):
        result = self._gpg.encrypt (
            data,
            recipient_key,
            sign = self._key,
            passphrase = self._password,
            always_trust = True
        );
        self._check_result (result);
        return str (result)

    def decode (self, encoded, correspondentKey):
        result = self._gpg.decrypt_verify (
            encoded,
            correspondentKey,
            passphrase = self._password,
            always_trust = True
        )
        self._check_result (result)
        return str (result)


class GpgIn (Tool):
    '''
    Расшифровщик POST-данных. ID клиентского ключа берет из URL (последняя часть пути)
    '''
    def __init__ (self):
        super (GpgIn, self).__init__(
            point = 'before_request_body',
            callable = self.run,
            name = 'gpg_in',
            priority = 80
        )

    def processor (self, entity):
        if not entity.headers.get (ntou ('Content-Length'), ntou ('')):
            raise cherrypy.HTTPError (411)

        request = cherrypy.serving.request
        encoder = Encoder (
            homedir = request._gpg_homedir,
            keyFingerprint = request._gpg_key,
            keyPassword = request._gpg_password
        )
        if not encoder.public_key_exists (request._gpg_client_key):
            raise Exception ('Invalid key')
        encoded = entity.fp.read ()
        decoded = encoder.decode (encoded, request._gpg_client_key)
        dict.update (
            request.headers,
            {
                'Content-Length': len (decoded),
                'Content-Type': request._gpg_target_ct if request._gpg_target_ct != None else entity.content_type
            }
        )
        request.body = RequestBody (
            SizedReader (
                StringIO (decoded),
                len (decoded),
                request.body.maxbytes
            ),
            request.headers,
            request_params = request.params
        )
        if request.process_request_body:
            request.body.process ()

    def run (self, homedir, key, password, content_types = 'application/pgp-encrypted', force = False, target_ct = None):
        request = cherrypy.serving.request
        request._gpg_force = force
        request._gpg_homedir = homedir
        request._gpg_key = key
        request._gpg_password = password
        request._gpg_target_ct = target_ct

        path = request.path_info.strip ('/')
        request._gpg_client_key = path [path.rfind ('/') + 1:]

        if force:
            request.body.processors [request.headers.get ('Content-Type')] = self.processor
        else:
            if isinstance (content_types, basestring):
                content_types = [content_types]
            for ct in content_types:
                request.body.processors [ct] = self.processor


class GpgOut (HandlerWrapperTool):
    '''
    Шифровальщик выходных данных
    '''
    def __init__ (self):
        super (GpgOut, self).__init__ (self.run, point = 'before_handler', name = 'gpg_out', priority = 10)

    def callable (self, content_type = 'application/pgp-encrypted'):
        cherrypy.serving.request._gpg_out_ct = content_type
        super (GpgOut, self).callable ()

    def run (self, nextHandler, *args, **kwargs):
        request = cherrypy.serving.request
        encoder = Encoder (
            homedir = request._gpg_homedir,
            key_fingerprint = request._gpg_key,
            key_password = request._gpg_password
        )
        if not encoder.public_key_exists (request._gpg_client_key):
            raise Exception ('Invalid key')
        try:
            response = nextHandler (*args, **kwargs)
        except:
            request.error_response ()
            response = cherrypy.response.body
        cherrypy.response.headers ['Content-Type'] = request._gpg_out_ct
        if not isinstance (response, basestring):
            response = ''.join (response)
        result = encoder.encode (response, request._gpg_client_key)
        cherrypy.response.headers ['Content-Length'] = len (result)
        return result
