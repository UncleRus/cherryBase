# -*- coding: utf-8 -*-

from cherrybase.utils import PoolsCatalog
import functools


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
                    try:
                        session.flush ()
                        session.commit ()
                    except:
                        session.rollback ()
                        session.expunge_all ()
                        raise
                return result
            except:
                session.rollback ()
                session.expunge_all ()
                raise
        return _wrapped
    return _wrap
