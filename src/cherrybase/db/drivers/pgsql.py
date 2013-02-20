# -*- coding: utf-8 -*-

import psycopg2.extras

class _Connection (psycopg2.extensions.connection):

    _encoding = 'utf8'

    def __init__ (self, dsn, async = 0):
        psycopg2.extensions.connection.__init__ (self, dsn, async)
        self.set_client_encoding (self._encoding)
        self.cursor ().execute ('set bytea_output to escape')
        self.commit ()

    def cursor (self, name = None, cursor_factory = psycopg2.extras.DictCursor):
        if not name:
            return super (_Connection, self).cursor (cursor_factory = cursor_factory)
        else:
            return super (_Connection, self).cursor (name, cursor_factory = cursor_factory)

    def select_row (self, sql, args = None):
        cursor = self.cursor ()
        cursor.execute (sql, args)
        return cursor.fetchone ()

    def select_value (self, sql, args = None):
        cursor = self.cursor (cursor_factory = psycopg2.extensions.cursor)
        cursor.execute (sql, args)
        row = cursor.fetchone ()
        return row [0] if row else None

    def select_all (self, sql, args = None):
        cursor = self.cursor ()
        cursor.execute (sql, args)
        return cursor.fetchall ()

    def format (self, sql, args = None):
        return self.cursor ().mogrify (sql, args)


class PgSql (object):

    def __init__ (self, host = '127.0.0.1', port = '5432', dbname = 'postgres', user = 'postgres',
                password = '', encoding = 'utf8', min_connections = 0, max_connections = 40):

        from psycopg2 import pool

        class _EConnection (_Connection):
            _encoding = encoding

        self._pool = pool.ThreadedConnectionPool (
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
        result = self._pool.getconn ()
        result.rollback ()
        return result

    def free (self, connection):
        self._pool.putconn (connection)
