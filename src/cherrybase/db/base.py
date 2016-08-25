# -*- coding: utf-8 -*-

from cherrybase.utils import PoolsCatalog
import functools
import cherrypy
import logging
import time


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
                catalog.idle (pool_name, connection)
                return result
            except:
                try:
                    connection.rollback ()
                    catalog.idle (pool_name, connection)
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


def use_mongo (pool_name = 'default', position = 1):
    '''
    Декоратор, добавляет в параметры функции ссылку на объект подключения к NoSQL БД.
    Ссылка добавляется на позицию position в списке параметров, 0 - первый параметр.
    '''
    def _wrap (method):
        @functools.wraps (method)
        def _wrapped (*args, **kwargs):
            connection = catalog.get (pool_name)
            # подключение к БД, указанной в URI соединения:
            db_conn = connection.get_default_database ()
            _largs = list (args)
            _largs.insert (position, db_conn)
            # FIXME: в MongoDB отсутствует поддержка механизма транзакций
            # они отдаются на откуп программисту
            try:
                result = method (*_largs, **kwargs)
                return result
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


def auto_config (config, pool_name, prefix = '', section = None):
    '''
    Разбор секции конфигурации и создание соответствюущего пула подключения к БД.
    Конфигурация (или указанная секция) должна содержать параметр ``prefix + 'driver'``.
    По умолчанию, драйвер = sqlite.
    Секция может содержать любые параметры, являющиеся ключами атрибута ``defaults`` драйвера.
    
    :param config: dict-like конфигурация
    :param pool_name: Имя создаваемого пула
    :param prefix: Строка префикса, котора будет добавлена ко всем параметрам конфигурации
    :param section: Название раздела конфигурации, если None, то раздел не выбирается
    '''
    if section:
        config = config.get (section, {})

    driver_name = config.get (prefix + 'driver', 'sqlite')
    # FIXME : Переписать загрузку драйвера с использованием __import__ или importlib
    if driver_name == 'sqlite':
        from drivers.sqlite import Sqlite
        Driver = Sqlite
    elif driver_name == 'pgsql':
        from drivers.pgsql import PgSql
        Driver = PgSql
    elif driver_name == 'mysql':
        from drivers.mysql import MySql
        Driver = MySql
    elif driver_name == 'mongodb':
        from drivers.mongodb import MongoDb
        Driver = MongoDb

    defaults = Driver.defaults.copy ()
    defaults.update ({
        'min_connections': 5,
        'max_connections': 30,
        'timeout': 0
    })
    catalog [pool_name] = Driver (**{param: config.get (prefix + param, value) for param, value in defaults.iteritems ()})


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
        row = self.select_row (sql, args)
        return row [0] if row else None

    def select_all (self, sql, args = None):
        cursor = self.__execute (sql, args)
        result = cursor.fetchall ()
        cursor.close ()
        return result


import threading


def _synchronize (func):
    def _wrapped (self, *args, **kwargs):
        self._lock.acquire ()
        try:
            return func (self, *args, **kwargs)
        finally:
            self._lock.release ()
    return _wrapped


class ThreadedPool (object):

    class Empty (Exception):
        pass

    def __init__ (self, connector, min_connections, max_connections, timeout = 0, **kwargs):
        self.connector = connector
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.timeout = timeout
        self.kwargs = kwargs

        self.pool = []
        self.used = {}
        self.timeouts = {}

        self._refill ()

        self._lock = threading.Lock ()
        import thread
        self._thread = thread

    def _refill (self):
        for _ in xrange (len (self.pool) + len (self.used), self.min_connections):
            self._idleconn (self._connect ())

    def _connect (self, key = None):
        connection = self.connector (**self.kwargs)
        if key is not None:
            self.used [key] = connection
        else:
            self.pool.append (connection)
        return connection

    def _getconn (self):
        key = self._thread.get_ident ()
        result = None
        if key in self.used:
            result = self.used [key]
        elif self.pool:
            self.used [key] = self.pool.pop ()
            result = self.used [key]
        if result:
            if result in self.timeouts:
                del self.timeouts [result]
            return result
        if len (self.used) == self.max_connections:
            raise ThreadedPool.Empty ('Connection pool exausted')
        return self._connect (key)

    def _idleconn (self, connection):
        if self.timeout > 0:
            self.timeouts [connection] = time.time () + self.timeout

    def _putconn (self, connection):
        key = self._thread.get_ident ()
        if len (self.pool) < self.min_connections:
            self.pool.append (connection)
            if key in self.used:
                del self.used [key]
            self._idleconn (connection)
        else:
            connection.close ()

    def _removeconn (self, connection):
        key = self._thread.get_ident ()
        if key in self.used:
            del self.used [key]
        try:
            connection.close ()
        except:
            pass

        for thread_index in list(self.used.keys()):
            if self.used [thread_index] == connection:
                del self.used [thread_index]
        if connection in self.pool:
            self.pool.remove (connection)
        if connection in self.timeouts:
            del self.timeouts [connection]

        self._refill ()

    def __contains__ (self, conn):
        return conn in self.pool or conn in self.used.values ()

    get = _synchronize (_getconn)
    put = _synchronize (_putconn)
    remove = _synchronize (_removeconn)
    idle = _synchronize (_idleconn)

    @_synchronize
    def clean (self):
        now = time.time ()
        for conn in self.pool + self.used.values ():
            if self.timeouts.get (conn, now) < now:
                self._removeconn (conn)

