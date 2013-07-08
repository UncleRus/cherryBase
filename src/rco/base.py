# -*- coding: utf-8 -*-

from cherrybase import rpc, orm
from cherrybase.utils import to_int
import gnupg
import cherrypy
import cherrybase
import pkg_resources
from cherrypy import _cpconfig
from . import stdlib
from . import _secmodel as mdl
from cherrypy.lib import xmlrpcutil
import logging, sys
from . import BaseError
#import sqlalchemy.sql as sas


def config (name, default = None, strict = False):
    app = cherrypy.request.app
    return app.service.service_config (name, default, strict)


class SecurityError (BaseError):
    pass


class Namespace (object):
    pass


class SecurityManager (object):

    _algos = {
        '0': None,
        '1': 'RSA',
        '2': 'RSA_E',
        '3': 'RSA_S',
        '16': 'ELGAMAL_E',
        '17': 'DSA',
        '16': 'ELGAMAL'
    }

    pool_name_format = '__{}__security_manager__'

    def __init__ (self, service, gpg_homedir, gpg_key, gpg_password):
        self.service = service
        self.gpg = gnupg.GPG (gnupghome = gpg_homedir)
        self.key = gpg_key
        self.password = gpg_password
        self.ifaces = {}
        self._update_keys ()

        # Готовим хранилище
        self.pool_name = self.pool_name_format.format (service.code)

        from cherrybase import db
        import cherrybase.db.drivers.sqlite as sqlite
        import cherrybase.orm.drivers.alchemy as alchemy

        min_conn = service.service_config ('security_manager.db_min_connections', 5)
        max_conn = service.service_config ('security_manager.db_max_connections', 30)

        # Создаем пул подключений к специальной БД
        db.catalog [self.pool_name] = sqlite.Sqlite (
            min_connections = min_conn,
            max_connections = max_conn,
            database = service.service_config ('security_manager.db_filename', ':memory:')
        )
        # Обертываем подключения в ORM
        orm.catalog [self.pool_name] = alchemy.SqlAlchemy (
            db_pool_name = self.pool_name,
            engine_url = 'sqlite://',
            pool_size = min_conn,
            pool_max_overflow = max_conn
        )
        # Достаем сессию алхимии из пула и создаем структуру БД
        session = orm.catalog.get (self.pool_name)
        mdl.Base.metadata.create_all (session.bind)
        # Синхронизируем БД и содержимое ключницы (удаляем из БД упоминания о несуществующих ключах)
        session.query (mdl.Rights).filter (~mdl.Rights.fingerprint.in_ (self.keys.keys ())).delete (synchronize_session = False)
        session.commit ()

    def _update_keys (self):
        self.keys = {}
        for key in self.gpg.list_keys ():
            if not key ['fingerprint'].endswith (self.key):
                self.keys [key ['fingerprint']] = {
                    'info': key ['uids'][0] if len (key ['uids']) > 0 else None,
                    'length': to_int (key ['length']),
                    'algo': self._algos.get (key ['algo'], key ['algo'])
                }

    def _prepare_keys (self, keys):
        if isinstance (keys, basestring):
            keys = [keys]
        for k in keys:
            if len (k) < 8:
                raise SecurityError ('Key id too short: {}'.format (k))
            if k.endswith (self.key) or self.key.endswith (k):
                raise SecurityError ('Cannot manipulate my own key: {}'.format (self.key), -2000)
        return keys

    def _prepare_methods (self, methods):
        return [methods] if isinstance (methods, basestring) else methods

    def connect_interface (self, iface):
        if not isinstance (iface, CryptoInterface):
            raise ValueError ('Interface is not instance of rco.CryptoInterface')
        self.ifaces [iface._mount_point] = iface.system.methods.keys ()

    def grant (self, methods, keys):
        '''
        session = orm.catalog.get (self.pool_name)
        keys = self._prepare_keys (keys)
        for method in self._prepare_methods (methods):
            for key in keys:
                if session.query (mdl.Rights).filter (
                        sas.and_ (
                            mdl.Rights.fingerprint == key,
                            sas.or_ (
                                sas.and_ (~mdl.Rights.method.endswith ('.'), mdl.Rights.method == method),
                                sas.and_ (mdl.Rights.method.endswith ('.'), sas.literal (method).startswith (mdl.Rights.method))
                            )
                        )
                    ).count () == 0:
                    session.add (mdl.Rights (key, method))
        '''
        # FIXME: Убрать заглушку
        pass

    def revoke (self, methods, keys):
        # FIXME: Убрать заглушку
        pass

    def rights (self, methods = None, keys = None):
        # FIXME: Убрать заглушку
        return {}

    def delete_keys (self, keys):
        keys = self._prepare_keys (keys)
        if not keys:
            return
        self._check_result (self.gpg.delete_keys (keys))
        session = orm.catalog.get (self.pool_name)
        session.query (mdl.Rights).filter (mdl.Rights.fingerprint.in_ (keys)).delete (synchronize_session = False)
        session.commit ()
        orm.catalog.put (self.pool_name, session)
        self._update_keys ()
        return

    def _check_result (self, result):
        if getattr (result, 'ok', False) or result:
            return
        raise SecurityError (
            '\n'.join ([line for line in getattr (result, 'stderr', 'gpg: {}'.format (getattr (result, 'status', 'Unknown error'))).splitlines () \
                if line.startswith ('gpg: ')]),
            - 2100
        )

    def import_keys (self, armored):
        result = self.gpg.import_keys (armored)
        self._update_keys ()
        return {res ['fingerprint']: (bool (to_int (res ['ok'])), res ['text'].strip ('\n')) for res in result.results}

    def export_keys (self, keys):
        return self.gpg.export_keys (self._prepare_keys (keys))

    def can_execute (self, iface, method):
        request = cherrypy.request
        if request.app.find_config ('/', 'full_access'):
            return True
        # FIXME: Сделать нормальную проверку
        return True

    def public_key_exists (self, key):
        if len (key) < 8:
            return False
        key = key.upper ()
        for item in self.gpg.list_keys ():
            if item.get ('fingerprint', '').upper ().endswith (key):
                return True
        return False

    def encrypt (self, data, recipient_key):
        result = self.gpg.encrypt (
            data,
            recipient_key,
            sign = self.key,
            passphrase = self.password,
            always_trust = True
        );
        self._check_result (result);
        return unicode (result)

    def decrypt (self, encoded, correspondent_key):
        result = self.gpg.decrypt_verify (
            encoded,
            correspondent_key,
            passphrase = self.password,
            always_trust = True
        )
        self._check_result (result)
        return unicode (result)


_xmlrpclib = xmlrpcutil.get_xmlrpclib ()


class EncryptedXmlrpcTool (cherrypy.Tool):
    '''Инструмент для замены tools.xmlrpc в криптоинтерфейсах'''

    def __init__ (self):
        super (EncryptedXmlrpcTool, self).__init__ (
            point = 'before_handler',
            callable = self.run,
            name = 'encrypted_xmlrpc',
            priority = 10
        )

    def _wrapper (self):
        self._on_error (**self._merged_args ())

    def _setup (self):
        cherrypy.serving.request.error_response = self._wrapper
        super (EncryptedXmlrpcTool, self)._setup ()

    def run (self):
        request = cherrypy.serving.request
        request.rco_security = request.app.service.security_manager

        path = request.path_info.strip ('/')
        request.rco_client = path [path.rfind ('/') + 1:]
        if not request.rco_security.public_key_exists (request.rco_client):
            raise SecurityError ('Unknown client key', -1001)

        request.rco_encrypted = request.body.read ()
        request.rco_decrypted = request.rco_security.decrypt (request.rco_encrypted, request.rco_client).encode ('utf-8')
        request.rco_encrypt_response = True


    def _on_error (self):
        e = sys.exc_info ()[1]
        if hasattr (e, 'args') and len (e.args) > 1:
            message = unicode (e.args [0])
            code = to_int (e.args [1], 1)
        else:
            message = '{}: {}'.format (type (e).__name__, unicode (e))
            code = 1
        body = _xmlrpclib.dumps (
            _xmlrpclib.Fault (code, message),
            methodresponse = 1,
            encoding = 'utf-8',
            allow_none = True
        )

        request = cherrypy.request
        response = cherrypy.response
        response.status = '200 OK'

        if getattr (request, 'rco_encrypt_response', False):
            ct = 'application/pgp-encrypted'
            body = request.rco_security.encrypt (body, request.rco_client).encode ('utf-8')
        else:
            ct = 'text/xml'

        response.headers ['Content-Type'] = ct
        response.headers ['Content-Length'] = len (body)
        response.body = body


cherrypy.tools.encrypted_xmlrpc = EncryptedXmlrpcTool ()


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
            raise SecurityError ('Access denied', -1000)
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

    _cp_config = {
        'tools.encrypted_xmlrpc.on': False,
        'tools.xmlrpc.on': True,
        'tools.xmlrpc.allow_none': True,
    }

    def __init__ (self, security_manager, code = None, version = None, title = None):
        self.meta = stdlib.Meta (security_manager, code, version, title)
        super (MetaInterface, self).__init__ ()


class Service (cherrybase.Application):

    def __init__ (self, package, basename, mode, vhosts, root = CryptoInterface, config = None):
        self.package = package

        # Готовим конфигурацию
        raw_config = {}
        _cpconfig.merge (
            raw_config,
            config or pkg_resources.resource_filename (package, '__config__/{}.conf'.format (mode))
        )
        self.service_conf = raw_config.get ('service', {})

        self.code = self.service_config ('code', package)

        sec_homedir = self.service_config ('security.homedir', require = True)
        sec_key = self.service_config ('security.key', require = True)
        sec_password = self.service_config ('security.password', require = True)

        # Создаем менеджер безопасности
        self.security_manager = SecurityManager (self, sec_homedir, sec_key, sec_password)

        _vhosts = [vhost + basename if vhost.endswith ('.') else vhost for vhost in vhosts]
        # Родительский конструктор
        super (Service, self).__init__ (
            name = self.code,
            vhosts = _vhosts,
            config = raw_config,
            routes = (
                ('/', root (self.security_manager), None),
                (
                    '/meta',
                    MetaInterface (
                        self.security_manager,
                        code = self.code,
                        version = self.service_config ('version', '1.0.0'),
                        title = self.service_config ('title', self.code)
                    ),
                    None
                ),
            )
        )
        self.main_name = _vhosts [0] + '/'
        self.app.service = self

    def service_config (self, name, default = None, require = False):
        if require and name not in self.service_conf:
            raise KeyError ('Service config value "{}" is not found'.format (name))
        return self.service_conf.get (name, default)

    def url (self, method_name):
        return 'http://{}:{}'.format (self.main_name, method_name)

