# -*- coding: utf-8 -*-

from cherrybase import rpc
import rco
import cherrypy

class TestLibrary (object):

    @rpc.expose
    @rco.tickets.use ()
    def hello (self, who):
        return 'Hello ' + who

    @rpc.expose
    def naming (self):
        service = cherrypy.request.app.service
        return service.naming.lookup ('test_service')


class Root (rco.CryptoInterface):

    def __init__ (self, *args, **kwargs):
        self.test = TestLibrary ()
        super (Root, self).__init__ (*args, **kwargs)
