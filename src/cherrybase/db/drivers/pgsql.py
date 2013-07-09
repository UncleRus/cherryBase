# -*- coding: utf-8 -*-

import psycopg2.extras
import psycopg2.pool
from ..base import ShortcutsMixin


class _Connection (psycopg2.extensions.connection, ShortcutsMixin):

    _encoding = 'utf8'

    def __init__ (self, *args, **kwargs):
        psycopg2.extensions.connection.__init__ (self, *args, **kwargs)
        psycopg2.extensions.register_type (psycopg2.extensions.UNICODE)
        self.set_client_encoding (self._encoding)
        self.cursor ().execute ('set bytea_output to escape')
        self.commit ()

    def cursor (self, name = None, cursor_factory = psycopg2.extras.DictCursor):
        return super (_Connection, self).cursor (*(name,) if name else (), cursor_factory = cursor_factory)


class PgSql (object):

    def __init__ (self, host = '127.0.0.1', port = 5432, dbname = 'postgres', user = 'postgres',
                password = '', encoding = 'utf8', min_connections = 0, max_connections = 40):

        class _EConnection (_Connection):
            _encoding = encoding

        self._pool = psycopg2.pool.ThreadedConnectionPool (
            min_connections,
            max_connections,
            'host={host} port={port} dbname={dbname} user={user} password={password}'.format (
                host = host,
                port = port,
                dbname = dbname,
                user = user,
                password = password
            ),
            connection_factory = _EConnection
        )

    def get (self):
        return self._pool.getconn ()

    def put (self, connection):
        self._pool.putconn (connection)
