# -*- coding: utf-8 -*-

from cherrybase.utils import PoolsCatalog

catalog = PoolsCatalog ('DB')

def use_db (pool_name = 'default', autocommit = True, position = 1):
    '''
    Декоратор, добавляет в параметры функции ссылку на объект подключения к БД.
    Ссылка добавляется на позицию position в списке параметров, 0 - первый параметр.
    '''
    def _wrap (method):
        def _wrapped (*args, **kwargs):
            global catalog
            connection = catalog.get (pool_name)
            _largs = list (args)
            _largs.insert (position, connection)
            try:
                result = method (*_largs, **kwargs)
                if (autocommit):
                    connection.commit ()
                return result
            except:
                connection.rollback ()
                raise
        return _wrapped
    return _wrap


import threading

class PoolError (Exception):
    pass

class ThreadedPool (object):

    def __init__ (self, connector, min_connections, max_connections, **kwargs):
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.connector = connector
        self._kwargs = kwargs

        self._pool = []
        self._used = {}

        for _i in xrange (0, min_connections):
            self._connect ()

        self._lock = threading.Lock ()
        import thread
        self._thread = thread

    def _connect (self, key = None):
        connection = self.connector (**self._kwargs)
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
