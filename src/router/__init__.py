# -*- coding: utf-8 -*-

from . import controllers
import rco
from cherrybase import orm, db
import cherrybase.db.drivers.sqlite as sqlite
import cherrybase.orm.drivers.alchemy as alchemy


def init_db (service):
    '''Инициализация БД и ORM-обертки'''
    # Добавляем пул подключений к БД в каталог
    min_conn = service.service_config ('router.min_connections', 5)
    max_conn = service.service_config ('router.max_connections', 30)
    db.catalog [__package__] = sqlite.Sqlite (
        min_connections = min_conn,
        max_connections = max_conn,
        database = service.service_config ('router.db_filename', ':memory:')
    )
    alchemy.auto_wrapper (__package__)


def get_applications (mode, basename):
    '''Главный метод создания сервиса'''
    # Создаем сервис без интерфейсов
    service = rco.Service (
        package = __package__,
        basename = basename,
        mode = mode,
        root = None
    )
    # Инициализируем БД
    init_db (service)
    # Добавляем интерфейсы
    service.tree.add ('/', controllers.Root (service.security_manager))
    service.add_meta ()

    return service
