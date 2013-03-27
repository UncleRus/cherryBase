# -*- coding: utf-8 -*-

from . import controllers

_vhosts = ('test.', 'www.test.')

def get_applications (mode, basename):
    from cherrypy import _cpconfig
    from cherrybase import Application, db
    import pkg_resources

    # Читаем конфиг
    config = {}
    _cpconfig.merge (config, pkg_resources.resource_filename (__package__, 'config/{}.conf'.format (mode)))

    def get_conf_global (entry, default):
        return config.get ('/', {}).get (entry, default)

    # Добавляем в каталог пулов БД нашу
    db.catalog ['test'] = db.drivers.PgSql (
        host = get_conf_global ('db_host', '127.0.0.1'),
        port = get_conf_global ('db_port', '5432'),
        dbname = get_conf_global ('db_name', ''),
        user = get_conf_global ('db_user', 'postgres'),
        password = get_conf_global ('db_password', 'secret')
    )

    # Возвращаем экземпляр приложения или список экземпляров
    return Application (
        name = 'test',
        vhosts = [vhost + basename if vhost [-1] == '.' else vhost for vhost in _vhosts],
        config = config,
        routes = (
            ('/', controllers.RootController (), None),
        )
    )
