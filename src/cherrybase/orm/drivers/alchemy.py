# -*- coding: utf-8 -*-

import logging
from logging.handlers import TimedRotatingFileHandler

import sqlalchemy
from sqlalchemy.orm import sessionmaker
from cherrybase import db

from cherrybase.conf import ConfigNamespace
import cherrypy


config = ConfigNamespace ('orm', {'log_filename': None});


class SqlAlchemy (object):

    class _GetConnection (object):

        def __init__ (self, db_pool_name):
            self.db_pool_name = db_pool_name

        def __call__ (self):
            return db.catalog.get (self.db_pool_name)

    def __init__ (self, db_pool_name = None, engine_url = 'postgresql://', pool_size = 10, pool_max_overflow = 60):
        self.db_pool_name = db_pool_name
        if db_pool_name:
            self.engine = sqlalchemy.create_engine (
                engine_url,
                pool = sqlalchemy.pool.QueuePool (
                    self._GetConnection (db_pool_name),
                    pool_size = pool_size,
                    max_overflow = pool_max_overflow,
                    use_threadlocal = True
                )
            )
        else:
            self.engine = sqlalchemy.create_engine (
                engine_url,
                poolclass = sqlalchemy.pool.QueuePool
            )

    def get (self):
        return sessionmaker (bind = self.engine)()

    def put (self, session):
        pass


logger = logging.getLogger ('sqlalchemy.engine')
if config.log_filename:
    logger.addHandler (TimedRotatingFileHandler (config.log_filename, 'midnight'))
if cherrypy.config.get ('debug', True):
    logger.setLevel (logging.INFO)
    handler = logging.StreamHandler ()
    handler.setLevel (logging.DEBUG)
    logger.addHandler (handler)
