# -*- coding: utf-8 -*-

import cherrypy
import logging

class Catalog (object):

    def __init__ (self):
        self.pools = {}
        self._thread_connections = {}
        cherrypy.engine.subscribe ('start_thread', self._start_thread)
        cherrypy.engine.subscribe ('stop_thread', self._stop_thread)

    def _start_thread (self, thread_index):
        cherrypy.thread_data.index = thread_index
        self._thread_connections [thread_index] = {}

    def _stop_thread (self, thread_index):
        if thread_index not in self._thread_connections:
            return
        for pool_name, connection in self._thread_connections [thread_index].items ():
            try:
                self.free (pool_name, connection)
            except:
                cherrypy.log.error (
                    'An error occured when releasing connection to pool {}'.format (pool_name),
                    context = 'DB',
                    severity = logging.WARNING,
                    traceback = True
                )
        del self._thread_connections [thread_index]

    def __iter__ (self):
        return iter (self.pools)

    def __contains__ (self, name):
        return name in self.pools

    def __setitem__ (self, name, pool):
        if name in self.pools:
            if self.pools [name] == pool:
                return
            raise ValueError ('Pool {} alredy defined'.format (name))
        self.pools [name] = pool

    def __getitem__ (self, name):
        return self.pools [name]

    def get (self, name):
        if name not in self.pools:
            raise ValueError ('Unknown pool {}'.format (name))
        connections = self._thread_connections [cherrypy.thread_data.index]
        if name not in connections:
            connections [name] = self.pools [name].get ()
        return connections [name]

    def free (self, name, connection):
        self.pools [name].free (connection)


catalog = Catalog ()

def use_db (pool_name = 'default', autocommit = True, position = 1):
    '''
    Декоратор, добавляет в параметры функции ссылку на объект подключения к БД.
    Ссылка добавляется на позицию position в списке параметров, 0 - первый параметр.
    '''
    def _wrap (method):
        def _wrapped (*args, **kwargs):
            global catalog
            _largs = list (args)
            connection = catalog.get (pool_name)
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
