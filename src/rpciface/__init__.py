# -*- coding: utf-8 -*-

from . import controllers
import rco

_vhosts = ('rpc.',)

def get_applications (mode, basename):
    from cherrypy import _cpconfig
    from cherrybase import Application, db
    import pkg_resources

    # Читаем конфиг
    config = {}
    _cpconfig.merge (config, pkg_resources.resource_filename (__package__, 'config/{}.conf'.format (mode)))

#    def  (entry, default = None):
#        return config.get ('/', {}).get (entry, default)
    get_conf_global = lambda entry, default = None: config.get ('/', {}).get (entry, default)

    security_manager = rco.SecurityManager (
        get_conf_global ('tools.gpg_in.homedir'),
        get_conf_global ('tools.gpg_in.key'),
        get_conf_global ('tools.gpg_in.password')
    )

    # Возвращаем экземпляр приложения или список экземпляров
    return Application (
        name = __name__,# 'rpciface',
        vhosts = [vhost + basename if vhost [-1] == '.' else vhost for vhost in _vhosts],
        config = config,
        routes = (
            ('/', controllers.Root (security_manager), None),
            (
                '/meta',
                rco.MetaInterface (
                    security_manager,
                    code = get_conf_global ('service.code', __name__),
                    version = get_conf_global ('service.version', '1.0.0'),
                    title = get_conf_global ('service.title', __name__)
                ),
                None
            ),
        )
    )
