# -*- coding: utf-8 -*-

import rco
import naming

class Root (rco.CryptoInterface):

    def __init__ (self, *args, **kwargs):
        self.routing = rco.Namespace ()
        self.routing.naming = naming.NamingLib ()
        super (Root, self).__init__ (*args, **kwargs)
