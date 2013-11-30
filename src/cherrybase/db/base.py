# -*- coding: utf-8 -*-

from cherrybase.utils import PoolsCatalog
import functools
import cherrypy
import logging


catalog = PoolsCatalog ('DB')


def use_db (pool_name = 'default', autocommit = True, position = 1):
    '''
    Декоратор, добавляет в параметры функции ссылку на объект подключения к БД.
    Ссылка добавляется на позицию position в списке параметров, 0 - первый параметр.
    '''
    def _wrap (method):
        @functools.wraps (method)
        def _wrapped (*args, **kwargs):
            connection = catalog.get (pool_name)
            _largs = list (args)
            _largs.insert (position, connection)
            try:
                result = method (*_largs, **kwargs)
                if (autocommit):
                    connection.commit ()
                return result
            except:
                try:
                    connection.rollback ()
                except:
                    cherrypy.log.error (
                        'Error in pool "{}" at rollback'.format (pool_name),
                        context = 'DB',
                        traceback = True,
                        severity = logging.ERROR
                    )
                    catalog.remove (pool_name, connection)
                raise
        return _wrapped
    return _wrap


class ShortcutsMixin (object):

    def __execute (self, sql, args):
        cursor = self.cursor ()
        cursor.execute (sql, args)
        return cursor

    def select_row (self, sql, args = None):
        cursor = self.__execute (sql, args)
        row = cursor.fetchone ()
        cursor.close ()
        return row

    def select_value (self, sql, args = None):
        cursor = self.__execute (sql, args)
        row = cursor.fetchone ()
        cursor.close ()
        return row [0] if row else None

    def select_all (self, sql, args = None):
        cursor = self.__execute (sql, args)
        result = cursor.fetchall ()
        cursor.close ()
        return result


import threading


class ThreadedPool (object):

    class Empty (Exception):
        pass

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
        result = None
        if key in self._used:
            result = self._used [key]
        elif self._pool:
            self._used [key] = self._pool.pop ()
            result = self._used [key]
        if result:
            return result
        if len (self._used) == self.max_connections:
            raise ThreadedPool.Empty ('Connection pool exausted')
        return self._connect (key)

    def _putconn (self, connection):
        key = self._thread.get_ident ()
        if len (self._pool) < self.min_connections:
            self._pool.append (connection)
            if key in self._used:
                del self._used [key]
        else:
            connection.close ()

    def _removeconn (self, connection):
        key = self._thread.get_ident ()
        if key in self._used:
            del self._used [key]
        try:
            connection.close ()
        except:
            pass

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

    def remove (self, connection):
        self._lock.acquire ()
        try:
            return self._removeconn (connection)
        finally:
            self._lock.release ()

