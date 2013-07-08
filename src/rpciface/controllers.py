# -*- coding: utf-8 -*-

from cherrybase import rpc
import rco

class TestLibrary (object):

    @rpc.expose
    @rco.tickets.use ()
    def hello (self, who):
        return 'Hello ' + who


class Root (rco.CryptoInterface):

    def __init__ (self, *args, **kwargs):
        self.test = TestLibrary ()
        super (Root, self).__init__ (*args, **kwargs)
