# -*- coding: utf-8 -*-

from cherrybase import rpc

class TestLibrary (object):

    @rpc.expose
    def hello (self, who):
        return 'Hello ' + who


class Root (rpc.Controller):

    def __init__ (self, *args, **kwargs):
        self.test = TestLibrary ()
        super (Root, self).__init__ (*args, **kwargs)
