# -*- coding: utf-8 -*-

import MySQLdb.cursors as mcur
import MySQLdb.connections as mconn

from ..base import ThreadedPool, ShortcutsMixin

class _Connection (mconn.Connection, ShortcutsMixin):
    pass

class MySql (ThreadedPool):

    def __init__ (self, min_connections = 0, max_connections = 40, *args, **kwargs):
        kwargs.update ({'cursorclass': mcur.DictCursor})
        super (MySql, self).__init__ (_Connection, min_connections, max_connections, **kwargs)
