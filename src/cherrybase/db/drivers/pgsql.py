# -*- coding: utf-8 -*-

import psycopg2.extras
from ..base import ThreadedPool, ShortcutsMixin


class _Connection (psycopg2.extensions.connection, ShortcutsMixin):

    def __init__ (self, *args, **kwargs):
        encoding = kwargs.get ('encoding', 'utf8')
        if 'encoding' in kwargs:
            del kwargs ['encoding']
        psycopg2.extensions.connection.__init__ (self, *args, **kwargs)
        psycopg2.extensions.register_type (psycopg2.extensions.UNICODE)
        self.set_client_encoding (encoding)
        # параметр "bytea_output" устанавливаем с 9-ой версии:
        if self.server_version >= 90000:
            cursor = self.cursor ()
            cursor.execute ('set bytea_output to escape')
            cursor.close ()
        self.commit ()

    def cursor (self, name = None, cursor_factory = psycopg2.extras.DictCursor):
        return super (_Connection, self).cursor (*(name,) if name else (), cursor_factory = cursor_factory)

    def is_connected (self):
        try:
            cursor = self.cursor ()
            cursor.execute ('select 1')
            cursor.close ()
            return True
        except:
            return False


class PgSql (ThreadedPool):

    defaults = {
        'host': '127.0.0.1',
        'port': '5432',
        'dbname': 'postgres',
        'user': 'postgres',
        'password': 'secret'
    }

    def __init__ (self, min_connections = 0, max_connections = 40, timeout = 0, **kwargs):
        super (PgSql, self).__init__ (
            _Connection,
            min_connections,
            max_connections,
            timeout,
            dsn = 'host={host} port={port} dbname={dbname} user={user} password={password}'.format (**kwargs),
            encoding = kwargs.get ('encoding', 'utf8')
        )
