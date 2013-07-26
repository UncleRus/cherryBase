# -*- coding: utf-8 -*-

from cherrybase import rpc
import cherrypy
import cherrybase
import pkg_resources
from cherrypy import _cpconfig
from . import stdlib, security, BaseError, _xmlrpclib
import logging


def config (name, default = None, strict = False):
    '''
    Получить значение настройки приложения.
    Может быть использован только в рамках обработчика запроса.
    
    :param name: Имя настройки
    :param default: Значение по умолчанию
    :param strict: Если True, то выбросить исключение при отсутствии параметра
    :returns: Значение параметра
    '''
    app = cherrypy.request.app
    return app.service.service_config (name, default, strict)


def prepare_config (conf, package):
    '''
    Метод подготовки конфигурации сервиса.
    
    :param conf: dict конфигурации
    :param package: имя пакета приложения (сервиса)
    '''
    pkg_path = pkg_resources.resource_filename (package, '')
    if isinstance (conf, list):
        for item in conf:
            if isinstance (item, basestring):
                item = item.format (PKG_PATH = pkg_path, PKG_NAME = package)
            elif isinstance (item, (dict, list)):
                prepare_config (item, package)
    elif isinstance (conf, dict):
        for key in conf:
            if isinstance (conf [key], basestring):
                conf [key] = conf [key].format (PKG_PATH = pkg_path, PKG_NAME = package)
            elif isinstance (conf [key], (dict, list)):
                prepare_config (conf [key], package)


class Namespace (object):
    '''
    Пространство имен XML-RPC интерфейса
    '''
    pass


class CryptoInterface (rpc.Controller):
    '''
    Базовый класс для всех шифрованных RPC-интерфейсов
    '''
    _cp_config = {
        'tools.encrypted_xmlrpc.on': True
    }

    def __init__ (self, security_manager, mount_point = '/'):
        self._mount_point = mount_point
        self._security = security_manager
        if mount_point == '/':
            self.control = Namespace ()
            self.control.keyring = stdlib.Keyring (self._security)
            self.control.access = stdlib.Access (self._security)
            self.callbacks = Namespace ()
        super (CryptoInterface, self).__init__ ()
        self._security.connect_interface (self)

    def _call_method (self, method, name, args, vpath, parameters):
        if not self._security.can_execute (self, name):
            raise security.SecurityError ('Access denied', -1000)
        return super (CryptoInterface, self)._call_method (method, name, args, vpath, parameters)

    def default (self, *vpath, **params):
        '''Обработчик по умолчанию'''
        request = cherrypy.request
        response = cherrypy.response

        try:
            rpc_params, rpc_method = _xmlrpclib.loads (request.rco_decrypted)
        except:
            request.app.log.error ('Invalid request', 'RPC', logging.WARNING, True)
            raise BaseError ('Invalid request', -32700)

        method = self._find_method (rpc_method)
        if method:
            result = self._call_method (method, rpc_method, rpc_params, vpath, params)
        else:
            raise BaseError ('Method "{}" not found'.format (rpc_method), -32601)

        body = self._security.encrypt (
            _xmlrpclib.dumps (
                (result,),
                methodresponse = 1,
                encoding = 'utf-8',
                allow_none = 1
            ),
            request.rco_client
        )

        response.status = '200 OK'
        response.headers ['Content-Type'] = 'application/pgp-encrypted'
        response.headers ['Content-Length'] = len (body)
        response.body = body
        return body

    default.exposed = True


class MetaInterface (rpc.Controller):
    '''
    Стандартный нешифрованный интерфейс meta
    '''
    _cp_config = {
        'tools.encrypted_xmlrpc.on': False,
        'tools.xmlrpc.on': True,
        'tools.xmlrpc.allow_none': True,
    }

    def __init__ (self, security_manager, code = None, version = None, title = None):
        self.meta = stdlib.Meta (security_manager, code, version, title)
        super (MetaInterface, self).__init__ ()


class Service (cherrybase.Application):
    '''
    Базовый класс сервиса.
    Все приложения, выполненные в рамках облачной концепции RCO,
    должны базироваться на этом классе вместо cherrybase.Application 
    '''
    def __init__ (self, package, basename, mode, root = None, config = None):
        self.package = package

        # Готовим конфигурацию
        raw_config = {
            '/' : {
                'tools.encode.on': True,
                'tools.gzip.on': True,
                'tools.gzip.mime_types': ['text/*', 'application/pgp-encrypted']
            }
        }
        _cpconfig.merge (
            raw_config,
            config or pkg_resources.resource_filename (package, '__config__/{}.conf'.format (mode))
        )
        prepare_config (raw_config, package)

        self.service_conf = raw_config.get ('service', {})

        self.code = self.service_config ('code', package)
        self.vhosts = self.service_config ('vhosts', [self.code + '.'])
        if isinstance (self.vhosts, basestring):
            self.vhosts = [self.vhosts]

        sec_homedir = self.service_config ('security.homedir', strict = True)
        sec_key = self.service_config ('security.key', strict = True)
        sec_password = self.service_config ('security.password', strict = True)

        # Создаем менеджер безопасности
        self.security_manager = security.Manager (self, sec_homedir, sec_key, sec_password)

        _vhosts = [vhost + basename if vhost.endswith ('.') else vhost for vhost in self.vhosts]
        self.main_name = _vhosts [0] + '/'

        # Создаем клиента роутинга
        if self.service_config ('naming.on', True):
            from . import naming
            self.naming = naming.NamingProxy (self)

        # Родительский конструктор
        super (Service, self).__init__ (
            name = self.code,
            vhosts = _vhosts,
            config = raw_config
        )
        self.app.service = self
        if root:
            self.tree.add ('/', root (self.security_manager))
            self.add_meta ()

    def add_meta (self):
        self.tree.add (
            '/meta',
            MetaInterface (
                self.security_manager,
                code = self.code,
                version = self.service_config ('version', '1.0.0'),
                title = self.service_config ('title', self.code)
            )
        )

    def service_config (self, name, default = None, strict = False):
        if strict and name not in self.service_conf:
            raise KeyError ('Service config value "{}" is not found'.format (name))
        return self.service_conf.get (name, default)

    def url (self, method_name = None):
        return ('http://{}:{}' if method_name else 'http://{}').format (self.main_name, method_name)

