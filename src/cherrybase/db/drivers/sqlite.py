# -*- coding: utf-8 -*-

import sqlite3
from ..base import ThreadedPool

class Sqlite (ThreadedPool):

    def __init__ (self, min_connections = 0, max_connections = 40, *args, **kwargs):
        super (Sqlite, self).__init__ (sqlite3.connect, min_connections, max_connections, check_same_thread = False, **kwargs)
