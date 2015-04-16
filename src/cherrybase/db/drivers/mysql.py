# -*- coding: utf-8 -*-

from ..base import ThreadedPool, ShortcutsMixin
from MySQLdb.connections import Connection
from MySQLdb.cursors import DictCursor
from MySQLdb import MySQLError
import os


class _Connection (Connection, ShortcutsMixin):

    default_cursor = DictCursor

    def __init__ (self, *args, **kwargs):
        super (_Connection, self).__init__ (*args, **kwargs)
        self.query ('set WAIT_TIMEOUT=%d' % 31536000 if os.name == 'posix' else 2147483)
        self.store_result ()

    def is_connected (self):
        try:
            self.ping ()
            return True
        except MySQLError:
            return False


class MySql (ThreadedPool):

    defaults = {
        'host': '127.0.0.1',
        'port': 3306,
        'unix_socket': '',
        'db': 'mysql',
        'user': 'root',
        'passwd': '',
        'charset': 'utf8',
        'compress': False
    }

    def __init__ (self, min_connections = 0, max_connections = 40, timeout = 0, **kwargs):
        super (MySql, self).__init__ (_Connection, min_connections, max_connections, timeout, **kwargs)

