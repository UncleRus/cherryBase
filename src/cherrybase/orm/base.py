# -*- coding: utf-8 -*-

from cherrybase.utils import PoolsCatalog
import functools
import cherrypy
import logging


catalog = PoolsCatalog ('ORM')


def use_orm (pool_name = 'default', autocommit = True, position = 1):
    '''
    Декоратор, добавляет в параметры функции ссылку на объект ORM-сессии.
    Ссылка добавляется на позицию position в списке параметров, 0 - первый параметр.
    '''
    def _wrap (method):
        @functools.wraps (method)
        def _wrapped (*args, **kwargs):
            session = catalog.get (pool_name)
            _largs = list (args)
            _largs.insert (position, session)
            try:
                result = method (*_largs, **kwargs)
                if autocommit:
                    session.flush ()
                    session.commit ()
                return result
            except:
                try:
                    session.rollback ()
                    session.expunge_all ()
                except:
                    cherrypy.log.error (
                        'Error in pool "{}" at rollback'.format (pool_name),
                        context = 'ORM',
                        traceback = True,
                        severity = logging.ERROR
                    )
                    raise
                raise
        return _wrapped
    return _wrap
