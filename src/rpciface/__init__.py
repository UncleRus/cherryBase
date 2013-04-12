# -*- coding: utf-8 -*-

from . import controllers

_vhosts = ('rpc.',)

def get_applications (mode, basename):
    from cherrypy import _cpconfig
    from cherrybase import Application, db
    import pkg_resources

    # Читаем конфиг
    config = {}
    _cpconfig.merge (config, pkg_resources.resource_filename (__package__, 'config/{}.conf'.format (mode)))

    def get_conf_global (entry, default):
        return config.get ('/', {}).get (entry, default)

    # Возвращаем экземпляр приложения или список экземпляров
    return Application (
        name = __name__,# 'rpciface',
        vhosts = [vhost + basename if vhost [-1] == '.' else vhost for vhost in _vhosts],
        config = config,
        routes = (
            ('/', controllers.Root (), None),
        )
    )
