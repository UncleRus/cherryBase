# -*- coding: utf-8 -*-

from ..base import ThreadedPool, ShortcutsMixin
from mysql_rco import Connection
import os


class _Connection (Connection, ShortcutsMixin):

    def __init__ (self, *args, **kwargs):
        super (_Connection, self).__init__ (*args, **kwargs)
        cursor = self.cursor ()
        cursor.execute ('set WAIT_TIMEOUT=%d' % 31536000 if os.name == 'posix' else 2147483)
        cursor.close ()



class MySql (ThreadedPool):

    defaults = {
        'host': '127.0.0.1',
        'port': 3306,
        'unix_socket': None,
        'database': None,
        'user': '',
        'password': ''
    }

    def __init__ (self, min_connections = 0, max_connections = 40, **kwargs):
        super (MySql, self).__init__ (_Connection, min_connections, max_connections, **kwargs)

