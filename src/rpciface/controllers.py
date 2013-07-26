# -*- coding: utf-8 -*-

from cherrybase import rpc
import rco
#import cherrypy

class TestLibrary (object):

    @rpc.expose
    @rco.tickets.use ()
    def hello (self, who):
        return 'Hello ' + who

    @rpc.expose
    def free_hello (self, who):
        return 'Hello ' + who

    @rpc.expose
    def naming (self):
        #app = cherrypy.request.app
        return rco.client.get_service ('test_service').test.free_hello ('double!!!!!')


class Root (rco.CryptoInterface):

    def __init__ (self, *args, **kwargs):
        self.test = TestLibrary ()
        super (Root, self).__init__ (*args, **kwargs)
