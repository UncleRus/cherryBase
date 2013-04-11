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
