# -*- coding: utf-8 -*-

import threading
import MySQLdb.cursors


class PoolError (Exception):
    pass


class MySql (object):

    def __init__ (self, min_connections = 0, max_connections = 40, *args, **kwargs):
        self.min_connections = min_connections
        self.max_connections = max_connections
        self._args = args
        self._kwargs = kwargs

        # Перекрываем курсор по умолчанию
        self._kwargs.update ({'cursorclass': MySQLdb.cursors.DictCursor})

        self._pool = []
        self._used = {}

        for _i in xrange (0, min_connections):
            self._connect ()

        self._lock = threading.Lock ()
        import thread
        self._thread = thread

    def _connect (self, key = None):
        connection = MySQLdb.connect (*self._args, **self._kwargs)
        if key is not None:
            self._used [key] = connection
        else:
            self._pool.append (connection)
        return connection

    def _getconn (self):
        key = self._thread.get_ident ()
        if key in self._used:
            return self._used [key]
        if self._pool:
            self._used [key] = self._pool.pop ()
            return self._used [key]
        if len (self._used) == self.maxconn:
            raise PoolError ('Connection pool exausted')
        return self._connect (key)

    def _putconn (self, connection):
        key = self._thread.get_ident ()
        if len (self._pool) < self.minconn:
            self._pool.append (connection)
            if key in self._used:
                del self._used [key]
        else:
            connection.close ()

    def get (self):
        self._lock.acquire ()
        try:
            return self._getconn ()
        finally:
            self._lock.release ()

    def put (self, connection):
        self._lock.acquire ()
        try:
            return self._putconn (connection)
        finally:
            self._lock.release ()

