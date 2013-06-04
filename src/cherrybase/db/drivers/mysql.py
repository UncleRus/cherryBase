# -*- coding: utf-8 -*-

import MySQLdb.cursors

from ..base import ThreadedPool

class MySql (ThreadedPool):

    def __init__ (self, min_connections = 0, max_connections = 40, *args, **kwargs):
        kwargs.update ({'cursorclass': MySQLdb.cursors.DictCursor})
        super (MySql, self).__init__ (MySQLdb.connect, min_connections, max_connections, **kwargs)
