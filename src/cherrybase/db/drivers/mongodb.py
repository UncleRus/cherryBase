# -*- coding: utf-8 -*-

from ..base import ThreadedPool


from pymongo import MongoClient


class _Connection (MongoClient):

    def is_connected (self):
        try:
            return self.alive ()
        except:
            return False


class MongoDb (ThreadedPool):

    defaults = {
        'host': '127.0.0.1',
        'port': 27017,
        'dbname': 'mongo_database',
        'user': 'root',
        'password': 'secret',
    }

    def __init__ (self, min_connections = 1, max_connections = 40, timeout = 0, **kwargs):
        super (MongoDb, self).__init__ (
            _Connection,
            min_connections,
            max_connections,
            timeout,
            host = 'mongodb://{user}:{password}@{host}:{port}/{dbname}'.format (**kwargs),
        )


