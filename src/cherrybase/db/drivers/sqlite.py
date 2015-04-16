# -*- coding: utf-8 -*-

import sqlite3
from ..base import ThreadedPool, ShortcutsMixin


class _Connection (sqlite3.Connection, ShortcutsMixin):
    pass


class Sqlite (ThreadedPool):

    defaults = {'database': ':memory:'}

    def __init__ (self, min_connections = 0, max_connections = 40, timeout = 0, *args, **kwargs):
        super (Sqlite, self).__init__ (_Connection, min_connections, max_connections, timeout, check_same_thread = False, **kwargs)
